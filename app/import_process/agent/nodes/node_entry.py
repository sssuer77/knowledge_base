import os
from os.path import splitext

from app.core.logger import logger
from app.import_process.agent.node_base import NodeBase
from app.import_process.agent.state import ImportGraphState

class NodeEntry(NodeBase):
    """
    节点: 入口节点 (EntryNode)
    作为图的 Entry Point，负责接收外部输入并决定流程走向。
    实现:
    1. 接收文件路径。
    2. 判断文件类型 (PDF/MD)。
    3. 设置 state 中的路由标记 (is_pdf_read_enabled / is_md_read_enabled)。
    """

    # 覆盖基类的 name 属性，标识节点名称
    name: str = "node_entry"

    def process(self, state: ImportGraphState) -> ImportGraphState:
        """
        LangGraph知识库导入工作流 - 入口节点
        执行链路：__start__ → 本节点 → route_after_entry(条件路由) → ... → 流程终止
        核心职责：初始化参数校验 | 自动判断文件类型(PDF/MD) | 设置解析开关 | 提取业务标识
        :param state: 必须包含 task_id(任务ID)、local_file_path(文件路径)、local_dir(流转到第二步的时候需要)
        :return: 新增/更新 is_pdf_read_enabled/is_md_read_enabled、pdf_path/md_path、file_title
        is_pdf_read_enabled/is_md_read_enabled：如果文件的扩展名是md，is_md_read_enabled=True，如果扩展名是pdf，is_pdf_read_enabled=True
        pdf_path/md_path：如果文件的扩展名是md，将local_file_path的值赋值给md_path，如果扩展名是pdf，将local_file_path的值赋值给pdf_path
        file_title：提取文件名
        """

        # 1. 核心参数提取与非空校验
        document_path = state.get("local_file_path", "")
        if not document_path:
            logger.error(f"核心参数缺失：工作流状态中未配置local_file_path，文件路径为空")
            return state

        # 2. 根据文件后缀判断类型，设置对应解析开关
        if document_path.endswith(".pdf"):
            logger.info(f"文件类型校验通过：{document_path} → PDF格式，开启PDF解析流程")
            state["is_pdf_read_enabled"] = True
            state["pdf_path"] = document_path
        elif document_path.endswith(".md"):
            logger.info(f"文件类型校验通过：{document_path} → MD格式，开启MD解析流程")
            state["is_md_read_enabled"] = True
            state["md_path"] = document_path
        else:
            logger.warning(f"文件类型校验失败：{document_path} → 不支持的格式，仅支持.pdf/.md")

        # 3. 提取不包含后缀的文件名，作为全局业务标识
        file_name = os.path.basename(document_path)
        state["file_title"] = splitext(file_name)[0]
        logger.info(f"文件业务标识提取完成：file_title = {state['file_title']}")

        return state


if __name__ == '__main__':
    from app.import_process.agent.state import create_default_state

    # 单元测试：覆盖不支持类型、MD、PDF三种场景

    # 测试1: 不支持的TXT文件
    test_state1 = create_default_state(
        task_id="test_entry_task_001",
        local_file_path="联想海豚用户手册.txt"
    )
    node_entry1 = NodeEntry()
    node_entry1(test_state1)

    # 测试2: MD文件
    test_state2 = create_default_state(
        task_id="test_entry_task_002",
        local_file_path="小米用户手册.md"
    )
    node_entry2 = NodeEntry()
    node_entry2(test_state2)

    # 测试3: PDF文件
    test_state3 = create_default_state(
        task_id="test_entry_task_003",
        local_file_path="小米用户手册.pdf"
    )
    node_entry3 = NodeEntry()
    node_entry3(test_state3)

    # 测试真实PDF文件:
    from app.core.logger import PROJECT_ROOT

    # 1. 测试文件路径
    local_file = os.path.join("doc", "H3C LA2608室内无线网关 用户手册-6W100-整本手册.pdf")
    local_file_path = os.path.join(PROJECT_ROOT, local_file)
    # 2. 输出目录
    local_dir = os.path.join(PROJECT_ROOT, "output")
    # 3. 定义初始状态
    initial_state = create_default_state(
        task_id="task_demo",
        local_file_path=local_file_path,
        local_dir=local_dir
    )
    node_entry = NodeEntry()
    node_entry(initial_state)