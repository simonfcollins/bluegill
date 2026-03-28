from bluegill_agent.exceptions.agent_exception import AgentError

class ToolNotFoundError(AgentError):
    pass

class ToolExecutionError(AgentError):
    pass

class ReadFileError(ToolExecutionError):
    pass

class WriteFileError(ToolExecutionError):
    pass

class EditFileError(ToolExecutionError):
    pass

class RunBashError(ToolExecutionError):
    pass