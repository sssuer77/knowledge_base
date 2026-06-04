import os
from typing import List, Tuple, Dict, Any

from langchain_core.messages import SystemMessage, HumanMessage
from pymilvus import DataType

from app.clients.milvus_utils import get_milvus_client
from app.core.load_prompt import load_prompt
from app.core.logger import logger
from app.import_process.agent.node_base import NodeBase
from app.import_process.agent.state import ImportGraphState
from app.lm.embedding_utils import generate_embeddings
from app.lm.lm_utils import get_llm_client
from app.utils.milvus_utils import escape_milvus_string
from app.utils.normalize_sparse_vector import normalize_sparse_vector

# --- 配置参数 (Configuration) # --- 配置参数 (Configuration) ---
# 大模型识别商品名称的上下文切片数：取前5个切片，避免上下文过长导致大模型输入超限
DEFAULT_ITEM_NAME_CHUNK_K = 5
# 单个切片内容截断长度：防止单切片内容过长，占满大模型上下文
SINGLE_CHUNK_CONTENT_MAX_LEN = 800
# 大模型上下文总字符数上限：适配主流大模型输入限制，默认2500
CONTEXT_TOTAL_MAX_CHARS = 2500

class NodeItemNameRecognition(NodeBase):
    """
    主体识别 (node_item_name_recognition)
    识别文档核心描述的物品/商品名称。
    实现:
    1. 取文档前几段内容。
    2. 调用 LLM 识别这篇文档讲的是什么东西 (如: "Fluke 17B+ 万用表")。
    3. 存入 state["item_name"] 用于后续数据幂等性清理。
    """

    # 覆盖基类的 name 属性，标识节点名称
    name: str = "node_item_name_recognition"

    def process(self, state: ImportGraphState) -> ImportGraphState:
        """
        LangGraph 核心节点：商品主体名称识别
        流程总览：
            1. 提取输入（文件标题+文本切片）
            2. 构建大模型上下文
            3. 调用大模型识别商品名称
            4. 回填商品名称到状态和切片
            5. 生成商品名称的稠密/稀疏向量
            6. 将数据存入Milvus向量数据库
        入参：
            state: 流程状态对象（ImportGraphState），包含上游节点的所有数据
        返回：
            state: 更新后的状态对象（包含识别出的item_name）
        """

        # --- 1. 提取并校验输入 ---
        file_title, chunks = self._step_1_get_inputs(state)

        # --- 2. 构建大模型识别的上下文 ---
        context = self._step_2_build_context(chunks)

        # 步骤3：调用大模型识别商品名称
        item_name = self._step_3_call_llm(file_title, context)

        # 步骤4：回填商品名称到状态和切片
        self._step_4_update_chunks(state, chunks, item_name)

        # 步骤5：为商品名称生成稠密/稀疏向量
        dense_vector, sparse_vector = self._step_5_generate_vectors(item_name)

        # 步骤6：将数据存入Milvus向量数据库
        self._step_6_save_to_milvus(state, file_title, item_name, dense_vector, sparse_vector)

        # 打印识别结果（调试用）
        logger.info(f"--- 识别完成: {item_name} ---")

        return state

    def _step_1_get_inputs(self, state: ImportGraphState) -> Tuple[str, List[Dict]]:
        """
        步骤 1: 接收并校验流程输入（商品名称识别的前置数据处理）
        核心作用：
            1. 从流程状态中提取文件标题、文本切片核心数据
            2. 做多层空值兜底，避免后续流程因空值报错
            3. 基础数据类型校验，保证下游流程输入有效性
        依赖的状态数据（上游节点产出）：
            - state["file_title"]: 上游提取的文件标题（优先使用）
            - state["file_name"]: 原始文件名（file_title为空时兜底）
            - state["chunks"]: 文本切片列表（每个切片为字典，含title/content等字段）
        返回值：
            Tuple[str, List[Dict]]: (处理后的文件标题, 校验后的文本切片列表)
        """
        # 多层兜底获取文件标题：优先file_title → 其次file_name → 空字符串
        file_title = state.get("file_title", "") or state.get("file_name", "")
        # 获取文本切片列表：空值时返回空列表，避免后续遍历报错
        chunks = state.get("chunks") or []

        # 二次兜底：file_title仍为空时，尝试从第一个有效切片中提取
        if not file_title:
            if chunks and isinstance(chunks[0], dict):
                file_title = chunks[0].get("file_title", "")
                logger.warning("state中无有效file_title，已从第一个切片中提取兜底标题")

        # 空值日志提示：文件标题为空时不中断流程，仅记录警告
        if not file_title:
            logger.warning("state中缺少file_title和file_name，后续大模型识别可能精度下降")

        # 数据类型校验：确保chunks为有效非空列表，否则返回空列表
        if not isinstance(chunks, list) or not chunks:
            logger.warning("state中chunks为空或非列表类型，无法进行商品名称识别")
            return file_title, []

        logger.info(f"步骤1：输入校验完成，获取到{len(chunks)}个有效文本切片")
        return file_title, chunks




    def _step_2_build_context(self, chunks: List[Dict], k: int = DEFAULT_ITEM_NAME_CHUNK_K, max_chars: int = CONTEXT_TOTAL_MAX_CHARS) -> str:
        """
        步骤 2: 构造大模型商品名称识别的标准化上下文
        核心作用：
            1. 限制切片数量：仅取前k个切片，避免上下文过长
            2. 限制字符长度：单切片+总上下文双重字符限制，适配大模型输入上限
            3. 格式化内容：带序号的结构化格式，提升大模型识别精度
            4. 过滤无效切片：跳过空内容/非字典类型切片，保证上下文有效性
        参数说明：
            chunks: 文本切片列表（每个元素为字典，需包含"title"和"content"键）
            k: 最大取片数，默认5个（可通过配置调整）
            max_chars: 上下文总字符数上限，默认2500（适配大模型输入限制）
        返回值：
            str: 格式化后的上下文字符串（直接传给大模型，空切片时返回空字符串）
        """
        # 空切片直接返回空字符串，无需后续处理
        if not chunks:
            return ""

        # 存储格式化后的切片片段，保证上下文结构化
        parts: List[str] = []
        # 统计已拼接字符数，用于控制总长度不超限
        total_chars = 0

        # 遍历前k个切片，避免上下文过长
        for idx, chunk in enumerate(chunks[:k]):
            # 跳过非字典类型切片，防止键取值报错
            if not isinstance(chunk, dict):
                logger.debug(f"第{idx+1}个切片非字典类型，已过滤")
                continue

            # 提取切片标题和内容，去首尾空格，过滤无效字符
            chunk_title = chunk.get("title", "").strip()
            chunk_content = chunk.get("content", "").strip()

            # 标题和内容均为空，跳过该无效切片
            if not (chunk_title or chunk_content):
                logger.debug(f"第{idx+1}个切片为空白内容，已过滤")
                continue

            # 单切片内容截断：防止单个切片内容过长占满上下文
            if len(chunk_content) > SINGLE_CHUNK_CONTENT_MAX_LEN:
                chunk_content = chunk_content[:SINGLE_CHUNK_CONTENT_MAX_LEN]
                logger.debug(f"第{idx+1}个切片内容过长，已截断至{SINGLE_CHUNK_CONTENT_MAX_LEN}字符")

            # 结构化格式化切片：带序号+标题+内容，提升大模型识别效率
            piece = f"【切片{idx + 1}】\n标题：{chunk_title} \n内容：{chunk_content}"
            parts.append(piece)
            # 累计字符数，包含分隔符
            total_chars += len(piece)

            # 总字符数超限时立即停止拼接，避免大模型输入超限
            if total_chars > max_chars:
                logger.info(f"上下文总字符数即将超限（{max_chars}），已停止拼接后续切片")
                break

        # 用空行分隔切片片段，拼接为最终上下文，最后一次去重空格
        context = "\n\n".join(parts).strip()
        # 最终二次截断，确保绝对不超限
        final_context = context[:max_chars]
        logger.info(f"步骤2：上下文构建完成，最终长度{len(final_context)}字符")
        return final_context

    def _step_3_call_llm(self, file_title: str, context: str) -> str:
        """
        步骤 3: 调用大模型实现商品名称/型号精准识别
        核心逻辑：
            1. 上下文为空 → 直接返回file_title（兜底，无需调用大模型）
            2. 上下文非空 → 加载标准化prompt模板，构建大模型对话消息
            3. 调用大模型后对返回结果做清洗，过滤无效字符
            4. 大模型返回空/调用异常 → 均返回file_title兜底，保证流程不中断
        核心特性：
            - 提示词解耦：通过load_prompt加载本地模板，无需硬编码
            - 格式兼容：兼容不同LLM客户端返回格式，防止属性报错
            - 异常兜底：全异常捕获，大模型服务不可用时不影响主流程
        参数：
            file_title: 处理后的文件标题（异常/空值时的兜底值）
            context: 步骤2构建的结构化切片上下文（大模型识别的核心依据）
        返回值：
            str: 清洗后的商品名称（异常/空值时返回原始file_title）
        """
        logger.info("开始执行步骤3：调用大模型识别商品名称")

        # 上下文为空时，直接返回文件标题，跳过大模型调用
        if not context:
            logger.warning("上下文为空，跳过大模型调用，直接使用文件标题作为商品名称")
            return file_title

        try:
            # 加载商品名称识别prompt模板，动态传入文件标题和上下文
            human_prompt = load_prompt("item_name_recognition", file_title=file_title, context=context)
            # 加载系统提示词，定义大模型角色（商品识别专家，仅返回纯结果）
            system_prompt = load_prompt("product_recognition_system")
            logger.debug(
                f"大模型调用提示词构建完成，系统提示词长度{len(system_prompt)}，人类提示词长度{len(human_prompt)}")

            # 获取大模型客户端：json_mode=False，要求返回纯文本而非JSON格式
            llm = get_llm_client(json_mode=False)
            if not llm:
                logger.error("大模型客户端获取失败，使用文件标题兜底")
                return file_title

            # 标准化构建大模型对话消息：SystemMessage定义角色 + HumanMessage传递业务请求
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ]
            # 调用大模型并获取返回结果
            resp = llm.invoke(messages)

            # 兼容不同LLM客户端返回格式：优先取content字段，无则返回空字符串
            item_name = getattr(resp, "content", "").strip()
            # 清洗返回结果：过滤空格、换行、回车、制表符等无效字符
            item_name = item_name.replace(" ", "").replace("\n", "").replace("\r", "").replace("\t", "")

            # 清洗后结果为空，使用文件标题兜底
            if not item_name:
                logger.warning("大模型返回空内容，使用文件标题作为商品名称兜底")
                return file_title

            logger.info(f"步骤3：大模型识别商品名称成功，结果为：{item_name}")
            return item_name

        # 捕获所有异常：大模型调用超时、网络错误、格式错误等，均不中断主流程
        except Exception as e:
            logger.error(f"步骤3：大模型调用失败，原因：{str(e)}", exc_info=True)
            # 异常时返回文件标题兜底，保证流程继续执行
            return file_title