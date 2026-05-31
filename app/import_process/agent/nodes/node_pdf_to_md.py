import shutil
import time
import zipfile
from pathlib import Path

import requests

from app.conf.mineru_config import mineru_config
from app.import_process.agent.node_base import NodeBase
from app.import_process.agent.state import ImportGraphState
from app.core.logger import logger


class NodePdfToMd(NodeBase):
    """
    节点: PDF转Markdown (node_pdf_to_md)
    核心任务是将 PDF 非结构化数据转换为 Markdown 结构化数据。
    实现:
    1. 调用 MinerU (magic-pdf) 工具。
    2. 将 PDF 转换成 Markdown 格式。
    3. 将结果保存到 state["md_content"]。
    """

    # 覆盖基类的 name 属性，标识节点名称
    name: str = "node_pdf_to_md"

    def process(self, state: ImportGraphState) -> ImportGraphState:
        """
        LangGraph工作流节点：PDF转MD核心处理节点
        核心职责：路径校验 → MinerU上传解析 → 结果下载解压 → 读取MD内容并更新工作流状态
        :param state: 必须包含 task_id(任务ID)、pdf_path(pdf文件路径)、local_dir(输出文件路径)
        :return:  md_path(pdf转成md后存储的路径)、md_content(md文件的内容)
        """

        # 步骤1：校验PDF路径和输出目录
        pdf_path_obj, output_dir_obj = self._step_1_validate_paths(state)

        # 步骤2：上传PDF至MinerU并轮询解析结果
        zip_url = self._step_2_upload_and_poll(pdf_path_obj, output_dir_obj)

        # 步骤3：下载ZIP包并提取MD文件
        md_path = self._step_3_download_and_extract(zip_url, output_dir_obj, pdf_path_obj.stem)

        # 步骤 4：读取内容 (如果文件不存在或编码错误，直接抛出异常，由外层捕获)
        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        # 更新状态
        state["md_path"] = str(md_path)
        state["md_content"] = md_content

        return state