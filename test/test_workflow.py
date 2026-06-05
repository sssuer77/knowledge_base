# test/test_workflow.py:

import os

from app.import_process.agent.main_graph import KBImportWorkflow
from app.import_process.agent.state import create_default_state
from app.utils.path_util import PROJECT_ROOT
from app.core.logger import logger

# 测试完整流程

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
# 4. 创建工作流实例
kb_import_app = KBImportWorkflow()

final_state = kb_import_app.run(initial_state)
logger.info(f"工作流执行完成！最终状态: {final_state}")