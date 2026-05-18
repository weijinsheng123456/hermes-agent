#!/usr/bin/env python3
"""
工作流可视化编排引擎 - 核心定义

对标 n8n (34K⭐) 的工作流自动化系统。
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    """节点类型"""
    TRIGGER = "trigger"
    ACTION = "action"
    CONDITION = "condition"
    TRANSFORM = "transform"
    AGENT = "agent"


class NodeStatus(str, Enum):
    """节点状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowNode:
    """工作流节点"""
    id: str
    name: str
    type: NodeType
    config: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0})
    status: NodeStatus = NodeStatus.PENDING
    output: Optional[Any] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id, "name": self.name, "type": self.type.value,
            "config": self.config, "position": self.position,
            "status": self.status.value, "output": self.output, "error": self.error
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "WorkflowNode":
        return cls(
            id=data["id"], name=data["name"], type=NodeType(data["type"]),
            config=data.get("config", {}), position=data.get("position", {"x": 0, "y": 0}),
            status=NodeStatus(data.get("status", "pending")),
            output=data.get("output"), error=data.get("error")
        )


@dataclass
class WorkflowConnection:
    """节点连接"""
    id: str
    source: str
    target: str
    condition: Optional[str] = None
    label: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {"id": self.id, "source": self.source, "target": self.target,
                "condition": self.condition, "label": self.label}
    
    @classmethod
    def from_dict(cls, data: Dict) -> "WorkflowConnection":
        return cls(id=data["id"], source=data["source"], target=data["target"],
                   condition=data.get("condition"), label=data.get("label"))


@dataclass
class Workflow:
    """工作流定义"""
    id: str
    name: str
    description: str = ""
    version: str = "1.0"
    nodes: List[WorkflowNode] = field(default_factory=list)
    connections: List[WorkflowConnection] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    triggers: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id, "name": self.name, "description": self.description,
            "version": self.version,
            "nodes": [n.to_dict() for n in self.nodes],
            "connections": [c.to_dict() for c in self.connections],
            "variables": self.variables, "triggers": self.triggers
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Workflow":
        wf = cls(id=data["id"], name=data["name"], description=data.get("description", ""),
                 version=data.get("version", "1.0"), variables=data.get("variables", {}),
                 triggers=data.get("triggers", []))
        for n in data.get("nodes", []):
            wf.nodes.append(WorkflowNode.from_dict(n))
        for c in data.get("connections", []):
            wf.connections.append(WorkflowConnection.from_dict(c))
        return wf
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    @classmethod
    def from_json(cls, json_str: str) -> "Workflow":
        return cls.from_dict(json.loads(json_str))


class WorkflowEngine:
    """工作流执行引擎"""
    
    def __init__(self):
        self.workflows: Dict[str, Workflow] = {}
        self.execution_history: List[Dict] = []
    
    def register_workflow(self, workflow: Workflow):
        self.workflows[workflow.id] = workflow
    
    async def execute_workflow(self, workflow_id: str, context: Dict = None) -> Dict:
        """执行工作流"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"success": False, "error": f"Workflow not found: {workflow_id}"}
        
        execution_id = str(uuid.uuid4())
        start_time = datetime.now()
        context = {**(workflow.variables or {}), **(context or {}), "execution_id": execution_id}
        
        # 重置状态
        for node in workflow.nodes:
            node.status = NodeStatus.PENDING
            node.output = None
            node.error = None
        
        # 拓扑排序
        order = self._topological_sort(workflow)
        results = {}
        success = True
        
        for node_id in order:
            node = next((n for n in workflow.nodes if n.id == node_id), None)
            if not node or not self._should_execute(node, workflow, results):
                continue
            
            try:
                node.status = NodeStatus.RUNNING
                output = await self._execute_node(node, context)
                node.status = NodeStatus.SUCCESS
                node.output = output
                results[node_id] = {"status": "success", "output": output}
                context[f"node_{node_id}"] = output
            except Exception as e:
                node.status = NodeStatus.FAILED
                node.error = str(e)
                results[node_id] = {"status": "failed", "error": str(e)}
                if not node.config.get("continue_on_error", False):
                    success = False
                    break
        
        return {
            "execution_id": execution_id, "workflow_id": workflow_id,
            "success": success, "duration": (datetime.now() - start_time).total_seconds(),
            "node_results": results
        }
    
    def _topological_sort(self, workflow: Workflow) -> List[str]:
        graph = {n.id: [] for n in workflow.nodes}
        in_degree = {n.id: 0 for n in workflow.nodes}
        for c in workflow.connections:
            if c.source in graph and c.target in graph:
                graph[c.source].append(c.target)
                in_degree[c.target] += 1
        queue = [k for k, v in in_degree.items() if v == 0]
        result = []
        while queue:
            node = queue.pop(0)
            result.append(node)
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        return result
    
    def _should_execute(self, node: WorkflowNode, workflow: Workflow, results: Dict) -> bool:
        for c in workflow.connections:
            if c.target == node.id:
                src = results.get(c.source, {})
                if src.get("status") != "success":
                    return False
                if c.condition:
                    try:
                        if not eval(c.condition, {"__builtins__": {}}, src.get("output", {})):
                            return False
                    except Exception:
                        pass
        return True
    
    async def _execute_node(self, node: WorkflowNode, context: Dict) -> Any:
        # 简化执行逻辑
        if node.type == NodeType.TRIGGER:
            return {"triggered": node.config.get("type", "manual"), "time": datetime.now().isoformat()}
        elif node.type == NodeType.ACTION:
            action = node.config.get("action", "")
            return {"action": action, "executed": True}
        elif node.type == NodeType.CONDITION:
            expr = node.config.get("expression", "true")
            return {"condition": expr, "result": True}
        elif node.type == NodeType.AGENT:
            return {"task": node.config.get("task", ""), "completed": True}
        return {}


def workflow_create(name: str, description: str = "", triggers: List = None, variables: Dict = None) -> str:
    wf = Workflow(id=str(uuid.uuid4()), name=name, description=description,
                  triggers=triggers or [], variables=variables or {})
    return json.dumps({"success": True, "workflow": wf.to_dict()}, ensure_ascii=False, indent=2)


def workflow_add_node(workflow_json: str, node_id: str, node_name: str, node_type: str,
                      config: Dict = None, position: Dict = None) -> str:
    wf = Workflow.from_json(workflow_json)
    wf.nodes.append(WorkflowNode(id=node_id, name=node_name, type=NodeType(node_type),
                                  config=config or {}, position=position or {"x": 0, "y": 0}))
    return json.dumps({"success": True, "workflow": wf.to_dict()}, ensure_ascii=False, indent=2)


def workflow_connect(workflow_json: str, source_id: str, target_id: str,
                     condition: str = None, label: str = None) -> str:
    wf = Workflow.from_json(workflow_json)
    wf.connections.append(WorkflowConnection(id=f"conn_{uuid.uuid4().hex[:8]}",
                                              source=source_id, target=target_id,
                                              condition=condition, label=label))
    return json.dumps({"success": True, "workflow": wf.to_dict()}, ensure_ascii=False, indent=2)


def register_workflow_tools():
    from tools.registry import registry
    
    registry.register(name="workflow_create", toolset="workflow",
        schema={"name": "workflow_create", "description": "创建工作流",
                "parameters": {"type": "object", "properties": {
                    "name": {"type": "string"}, "description": {"type": "string"},
                    "triggers": {"type": "array"}, "variables": {"type": "object"}
                }, "required": ["name"]}},
        handler=lambda args, **kw: workflow_create(args.get("name", ""), args.get("description", ""),
                                                    args.get("triggers"), args.get("variables")))
    
    registry.register(name="workflow_add_node", toolset="workflow",
        schema={"name": "workflow_add_node", "description": "添加节点到工作流",
                "parameters": {"type": "object", "properties": {
                    "workflow_json": {"type": "string"}, "node_id": {"type": "string"},
                    "node_name": {"type": "string"}, "node_type": {"type": "string"},
                    "config": {"type": "object"}, "position": {"type": "object"}
                }, "required": ["workflow_json", "node_id", "node_name", "node_type"]}},
        handler=lambda args, **kw: workflow_add_node(args.get("workflow_json", ""), args.get("node_id", ""),
                                                      args.get("node_name", ""), args.get("node_type", ""),
                                                      args.get("config"), args.get("position")))
    
    registry.register(name="workflow_connect", toolset="workflow",
        schema={"name": "workflow_connect", "description": "连接两个节点",
                "parameters": {"type": "object", "properties": {
                    "workflow_json": {"type": "string"}, "source_id": {"type": "string"},
                    "target_id": {"type": "string"}, "condition": {"type": "string"},
                    "label": {"type": "string"}
                }, "required": ["workflow_json", "source_id", "target_id"]}},
        handler=lambda args, **kw: workflow_connect(args.get("workflow_json", ""), args.get("source_id", ""),
                                                     args.get("target_id", ""), args.get("condition"),
                                                     args.get("label")))

register_workflow_tools()
