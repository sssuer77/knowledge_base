# app/import_process/agent/nodes/node_demo.py
from app.core.logger import logger
from app.import_process.agent.node_base import NodeBase
from app.import_process.agent.state import ImportGraphState, create_default_state

class NodeDemo(NodeBase):
    name: str = "node_demo"
    def process(self, state: ImportGraphState) -> ImportGraphState:
        logger.info("当前节点的具体业务逻辑")
        logger.debug("当前节点的状态调试信息")

        return state

if __name__ == "__main__":
    node_demo = NodeDemo()
    node_state = create_default_state(
        task_id="task_demo"
    )
    # node_demo.process(state) #只执行业务逻辑
    node_demo(node_state) #包含日志、任务追踪、统一异常处理