This Module is developed based on OpenManus:
- https://github.com/mannaandpoem/OpenManus

# WenCFO Agent & OpenManus 系统整合文档

## 抽象理解

当用户提问后：

1、系统调用LLM API，将该提问分解为一系列agent任务，并编排flow

2、根据flow顺序，依次让不同的agent完成任务

3、每个agent完成任务的时候，根据需要调用不同的tool


## 一、项目背景与目标

- **背景说明**  
  WenCFO Agent 目前包含 backend、docs、www 三个主要部分，而 OpenManus 模块作为新加入的组件，提供了多代理系统的功能，支持任务规划、工具调用、沙箱安全执行等。  
  **目标**：整合 OpenManus 模块的强大功能到现有系统中，实现高效、灵活的多代理任务执行。

- **项目概述**  
  - **WenCFO Agent**：包含后端接口、文档及简单前端页面。  
  - **OpenManus 模块**：具备代理、流程规划、工具调用、沙箱环境等多个子系统，旨在复现 Manus AI 代理的功能。

---

## 二、进度记录与工作要求

- **文档版本**：1.0（2025-04-07）
- **已完成内容**：  
  - 初步整理 WenCFO Agent 与 OpenManus 模块的目录结构及各文件/文件夹的初步描述。  
  - 对所有尚未明确的内容均以 **[猜测]** 标记，后续将依据具体脚本内容进行更新。
- **工作要求**：  
  - 当前已建立基本文档框架，包含项目背景、整体结构、各模块初步说明以及后续任务清单。
  - 下一步计划：依次查看各具体脚本内容，更新【猜测】部分为准确描述，并讨论如何将各功能整合进现有系统。
  - 在更新的时候，用户（“我”）会给你（“人工智能/LLM/ChatGPT/Claude”）一个文件的名字和内容，你需要结合文件的内容和文档内容，修改对应部分的内容。如果文档无需修改，则只给出替换原本文件描述的内容。
  - 如果需要我提供更多的信息，你需要随时跟我说。如果我提供的信息不足以将猜测去掉，请你及时告诉我，而不要胡乱添加或修改文档内容。
  - 如果你有任何不确定的地方，都不能凭空添加或修改内容。
  - 请用markdown格式写。【这个主要是为了方便复制粘贴，所以请在整理好答案后输出的时候记住这一点】
  - 保持原本的格式不变。
  - 你可以参考其他已经完成的/非猜测部分的撰写内容和格式
  - 保留函数名、英文专有术语等

---

## 三、待补充与后续任务清单

- **待确认的模块与文件**：  
  - WenCFO Agent 中 backend、docs、www 的具体实现细节（目前以【猜测】标记）。  
  - OpenManus 模块中各子目录（agent、flow、mcp、prompt、sandbox、tool 等）的详细功能和调用关系。
- **后续任务**：  
  - 根据你逐步提供的具体文件内容，逐步完善每个模块的说明，更新【猜测】部分为准确描述。  
  - 整合 OpenManus 模块与现有系统时，需明确配置统一、接口设计、日志和异常处理机制等细节。
- **整合计划**：  
  - 先从部分功能（如工具调用、任务规划）入手，逐步构建适配层。  
  - 定义清晰接口，确保各模块协同工作并编写相应测试用例。

---

## 四、上下文参考信息

- **讨论摘要**：  
  - 目前我们已初步整理文档，记录了 WenCFO Agent 与 OpenManus 模块的整体结构及文件关系。
  - 后续将依据具体文件内容不断更新说明文档，确保在冷启动时能快速了解当前进度及下一步工作。
- **关键词和术语**：  
  - **agent**：代理相关的逻辑及接口。  
  - **flow**：任务流程规划和管理。  
  - **sandbox**：安全执行环境。  
  - **tool**：各类工具调用接口。  
  - **mcp**：多通道处理或任务管理相关模块。  
  - **prompt**：用于生成提示模板，指导大语言模型行为。  

---

## 五、WenCFO Agent 整体结构

系统目前包含以下主要部分：

- **backend**  
  - **main.py**  
    - **主要功能**：  
        - 基于 FastAPI 实现的后端服务，为 WenCFO Agent 提供聊天接口。  
        - 包含跨域配置、限速机制、与 DeepSeek API 的集成，以及日志记录功能。  
        - 处理客户端请求并返回流式响应。  

    - **主要组件与配置**：  
        - `FastAPI` 应用实例化 (`app`)。  
        - `CORS Middleware`：允许所有源访问 (`allow_origins=["*"]`)，实际部署时应进行修改。  
        - `Limiter`：基于 `slowapi` 实现的限速器，每个 IP 每分钟最多请求 5 次。  
        - `Logging`：配置为记录 `INFO` 级别及以上的日志信息。  

    - **API 路由**：  
        - `POST /api/chat`：处理聊天请求。  
        - 限速：每个 IP 每分钟最多请求 5 次。  
        - 请求体：JSON 格式，包含一个 `question` 字段。  
        - 响应：  
            - 成功时返回流式响应 (`StreamingResponse`)。  
            - 错误时返回 JSON 格式的错误信息。  

    - **DeepSeek 集成**：  
        - 使用 `OpenAI` SDK 进行 API 调用，指定 `base_url` 为 `https://api.deepseek.com`。  
        - 使用 `stream=True` 参数支持流式输出。  

    - **安全性注意事项**：  
        - API 密钥 (`api_key`) 硬编码在脚本中，应在生产环境中使用安全的配置方式管理密钥。  
        - 跨域策略应在部署时进行限制，避免开放给所有源。  
        - 日志记录中避免输出敏感信息。  


- **docs**  
  - 存放文档、备份文件（backup）及版本相关文件（V1），主要用于记录系统设计、使用说明和历史版本资料。 

- **www**  
  - **index.html**：前端页面，提供一个简单的界面与后端 FastAPI 接口交互。  
    - **主要功能**：  
      - 提供与 WenCFO Agent 的聊天接口交互界面。  
      - 包含输入框、发送按钮、消息显示区域，并支持流式响应展示。  
      - 实现了用户消息与服务器回复的前端显示。  
    - **主要组件与配置**：  
      - **页面布局与样式**：  
        - 使用 Flexbox 布局，使输入区域固定在页面底部。  
        - 设置聊天框为滚动容器 (`overflow-y: auto`)，确保消息历史不被遮挡。  
      - **用户输入与消息显示**：  
        - 输入框 (`<input>`) 用于接收用户问题，按下 Enter 或点击按钮即可发送。  
        - 按钮 (`<button>`) 提交问题，并触发 `send()` 函数。  
        - 用户消息与 AI 回复以不同样式 (`user` 和 `bot`) 显示在聊天框中。  
      - **与后端 API 的交互**：  
        - 请求方式：`POST` 请求发送到 `/api/chat` 接口。  
        - 数据格式：`JSON` 格式，包含 `question` 字段。  
        - 使用 `fetch()` 函数发送请求，并使用流式读取 (`ReadableStream`) 实时显示 AI 的回复。  
      - **异常处理与用户提示**：  
        - 当请求出错时，显示 “CFO：出错了，请稍后再试。”。  
        - 初始加载时显示欢迎消息，指导用户输入问题。  
      - **优化与功能改进**：  
        - 支持在输入框内按下 `Enter` 键发送消息。  
        - 提供用户与 AI 的消息分离显示样式，提升用户体验。  
        - 提示用户当前系统处于内测阶段，无保存功能。  

- **open_manus**  
  - 新加入的模块，提供多代理系统的功能，支持任务规划、工具调用、沙箱安全执行等。 **[猜测]**

---

## 六、OpenManus 模块结构与关键文件

OpenManus 模块通过多层次结构实现复杂任务的自动执行和工具集成，其目录结构及主要文件说明如下：

### 1. open_manus/app 目录

该目录为模块核心实现部分，包含如下子目录和文件：

#### A. agent 子目录
- **\_\_init\_\_.py**  
  - **主要功能**：  
    - 初始化 `agent` 模块，并加载相关代理类，包括：  
      - `BaseAgent`：定义代理的基础接口和行为。  
      - `BrowserAgent`：用于处理与浏览器相关的代理操作。  
      - `MCPAgent`：多通道处理（MCP）代理，用于管理复杂任务的并行处理。  
      - `ReActAgent`：实现代理响应机制，用于交互反馈或动态调整行为。  
      - `SWEAgent`：提供与软件工程相关的代理功能（如代码生成、调试等）。  
      - `ToolCallAgent`：负责调用各类工具的代理，用于执行外部工具接口。  
    - 定义了模块的公开接口列表 `__all__`，包括上述所有代理类。  

- **base.py**  
  - **主要功能**：  
    - 定义 `BaseAgent` 抽象基类，提供通用的代理功能框架，包括状态管理、内存管理和执行流程的核心逻辑。  
    - 强制所有子类实现 `step()` 方法，以定义具体的单步操作逻辑。  
    - 支持异步运行方式，通过 `run()` 方法启动代理的执行流程，并自动管理状态切换（`IDLE` -> `RUNNING` -> `FINISHED` / `ERROR`）。  
    - 提供消息管理接口，通过 `update_memory()` 将用户或系统的消息添加到内存中，并支持工具调用的上下文管理。  
    - 检测重复响应的机制 (`is_stuck()`) 并提供相应的处理方法 (`handle_stuck_state()`)。  
    - 提供 `messages` 属性用于读取或设置代理的所有消息。  
    - 与 `SANDBOX_CLIENT` 集成，确保在执行完成后清理资源。  

  - **主要组件与类**：  
    - `BaseAgent`：提供代理的核心抽象接口。  
    - `run()`：代理的主运行循环，支持自定义最大步数 (`max_steps`) 和逐步执行。  
    - `update_memory()`：将新的消息（文本或图片）添加到代理内存。  
    - `is_stuck()`：检测代理是否卡在重复的响应中。  
    - `handle_stuck_state()`：当检测到卡住状态时，修改 `next_step_prompt` 以调整策略。  
    - `step()`：抽象方法，子类必须实现，定义具体的单步操作。  
    - `messages` 属性：用于获取或设置代理内存中的消息列表。  


- **browser.py**  
  - **主要功能**：  
    - 定义 `BrowserAgent` 类，用于通过工具调用 (`BrowserUseTool`) 实现浏览器的控制和交互。  
    - 提供 `BrowserContextHelper` 辅助类，用于管理浏览器的状态获取和截图保存。  
    - 通过 `think()` 方法将浏览器状态信息注入到下一步提示 (`next_step_prompt`) 中，以便生成更加上下文相关的响应。  
    - 提供 `cleanup()` 方法用于在任务结束后清理浏览器资源。  

  - **主要组件与类**：  
    - `BrowserContextHelper`：辅助类，用于与 `BrowserUseTool` 交互，获取当前浏览器状态并格式化提示。  
      - `get_browser_state()`：获取当前浏览器状态，包括 URL、标题、标签页信息等。  
      - `format_next_step_prompt()`：基于浏览器状态生成下一步提示内容。  
      - `cleanup_browser()`：在任务完成后清理浏览器资源。  
    - `BrowserAgent`：继承自 `ToolCallAgent`，提供基于浏览器的自动化任务功能。  
      - `think()`：在每次决策过程中更新浏览器状态，并生成适当的提示内容。  
      - `cleanup()`：在任务完成后调用 `BrowserContextHelper` 进行资源清理。  
      - 可用工具 (`available_tools`)：包括 `BrowserUseTool` 和 `Terminate`。  
      - 工具选择策略 (`tool_choices`)：设置为 `ToolChoice.AUTO`，允许自动调用工具或自由响应。  


- **manus.py**  
  - **主要功能**：  
    - 定义 `Manus` 类，作为通用的多功能代理 (`ToolCallAgent`)。  
    - 提供对多种工具的集成，包括 `PythonExecute`、`BrowserUseTool`、`StrReplaceEditor` 和 `Terminate`。  
    - 支持通过 `BrowserContextHelper` 来与浏览器交互，并在必要时更新提示 (`next_step_prompt`)。  
    - 在 `think()` 方法中，根据工具使用情况动态调整 `next_step_prompt`，并在任务结束后还原原始提示内容。  
    - 提供 `cleanup()` 方法用于清理与浏览器相关的资源。  

  - **主要组件与类**：  
    - `Manus`：通用多功能代理，继承自 `ToolCallAgent`。  
      - `think()`：检查最近消息中是否使用了浏览器工具，并自动更新提示内容。  
      - `cleanup()`：调用 `BrowserContextHelper` 进行清理。  
      - 可用工具 (`available_tools`)：包括 `PythonExecute`、`BrowserUseTool`、`StrReplaceEditor`、`Terminate`。  
      - 工具选择策略 (`tool_choices`)：默认为 `ToolChoice.AUTO`，允许自动调用工具或自由响应。  
      - 与 `BrowserContextHelper` 集成，实现对浏览器状态的动态处理。  

- **mcp.py**  
  - **主要功能**：  
    - 定义 `MCPAgent` 类，用于与 MCP (Model Context Protocol) 服务器进行通信，并通过工具接口提供交互功能。  
    - 支持两种通信方式：标准输入输出 (`stdio`) 和服务器发送事件 (`sse`)。  
    - 提供工具的动态刷新机制，支持自动更新工具列表并检测工具的新增、移除或更改。  
    - 提供 `cleanup()` 方法用于在任务完成后关闭 MCP 连接。  
    - 在 `think()` 方法中，通过工具接口 (`MCPClients`) 与服务器交互。  

  - **主要组件与类**：  
    - `MCPAgent`：继承自 `ToolCallAgent`，提供与 MCP 服务器的交互功能。  
      - `initialize()`：配置并建立 MCP 连接，支持 `stdio` 和 `sse` 两种方式。  
      - `_refresh_tools()`：从服务器中动态刷新工具列表，并更新内存中的工具信息。  
      - `think()`：判断当前工具可用状态并决定下一步操作。  
      - `cleanup()`：在操作完成后关闭 MCP 连接。  
      - `run()`：启动代理并确保在操作完成后进行资源清理。  
      - `_handle_special_tool()`：处理特殊工具执行，如多媒体响应工具。  
      - `_should_finish_execution()`：判断是否应终止代理的执行。  

- **react.py**  
  - **主要功能**：  
    - 定义 `ReActAgent` 抽象基类，提供 `think` 和 `act` 两阶段的分离式任务执行框架。  
    - 支持自定义的 `think()` 和 `act()` 方法，由子类实现具体行为。  
    - 提供 `step()` 方法作为统一的执行接口，首先调用 `think()` 决定是否需要执行操作，然后调用 `act()` 执行。  
    - 允许代理保持状态 (`AgentState`) 并通过 `Memory` 存储上下文信息。  
    - 集成 `LLM` 模型用于自然语言处理和决策支持。  

  - **主要组件与类**：  
    - `ReActAgent`：一个支持 `Think` 和 `Act` 流程的通用抽象代理。  
      - `think()`：抽象方法，子类必须实现，用于判断当前状态并决定是否需要执行。  
      - `act()`：抽象方法，子类必须实现，用于执行所决定的操作。  
      - `step()`：调用 `think()` 和 `act()`，实现完整的单步执行流程。  
      - 使用 `LLM` 作为核心的决策引擎，并通过 `Memory` 存储上下文信息。  
      - 提供 `max_steps` 和 `current_step` 用于控制任务执行的步数限制。  

- **swe.py**  
  - **主要功能**：  
    - 定义 `SWEAgent` 类，用于实现自主软件工程 (SWE) 代理。  
    - 通过工具调用 (`ToolCallAgent`) 与系统工具（如 `Bash`、`StrReplaceEditor` 和 `Terminate`）进行交互。  
    - 支持执行代码、文本替换与编辑等任务。  
    - 提供 `SYSTEM_PROMPT` 作为初始系统提示。  
    - 配置可用工具集合 (`available_tools`) 和特殊工具 (`Terminate`) 用于终止任务。  

  - **主要组件与类**：  
    - `SWEAgent`：继承自 `ToolCallAgent`，专为软件工程相关任务设计。  
      - `available_tools`：包含 `Bash`（用于执行命令行指令）、`StrReplaceEditor`（用于字符串替换）、`Terminate`（用于终止任务）。  
      - `special_tool_names`：包含 `Terminate` 用于检测任务终止。  
      - `max_steps`：设置为 20，用于控制任务的最大执行步数。  
      - `system_prompt`：加载自 `app.prompt.swe` 的 `SYSTEM_PROMPT`。  

- **toolcall.py**  
  - **主要功能**：  
    - 定义 `ToolCallAgent` 类，用于处理工具调用与函数调用的代理。  
    - 提供了工具调用的完整执行流程，包括请求生成、工具调用、结果处理与异常捕获。  
    - 支持自动工具选择 (`ToolChoice.AUTO`)、工具调用必须 (`ToolChoice.REQUIRED`) 和工具调用禁止 (`ToolChoice.NONE`) 三种模式。  
    - 在执行过程中提供详细的日志记录与错误处理机制。  
    - 支持异步工具调用与清理操作。  

  - **主要组件与类**：  
    - `ToolCallAgent`：继承自 `ReActAgent`，用于处理工具调用与函数调用的代理。  
      - `think()`：生成工具调用请求并与 LLM 交互，支持工具选择策略与自定义提示。  
      - `act()`：执行工具调用并处理返回结果，支持多次调用与结果记录。  
      - `execute_tool()`：执行单个工具调用，支持错误捕获与日志记录。  
      - `_handle_special_tool()`：处理特殊工具的执行与状态管理。  
      - `cleanup()`：清理资源与工具实例，确保代理正常退出。  
      - `run()`：启动代理，支持自动清理操作。  
    - `available_tools`：工具集合，包含 `CreateChatCompletion()` 和 `Terminate()`。  
    - `tool_choices`：工具调用策略，支持 `AUTO`, `REQUIRED`, `NONE` 三种模式。  
    - `special_tool_names`：定义特殊工具的名称列表（如 `Terminate`）。  
    - `tool_calls`：记录当前任务中所有的工具调用信息。  
    - `max_steps`：限制任务执行的最大步数（默认：30）。  
    - `max_observe`：控制工具调用结果的最大观察量。  

  - **日志与异常处理**：  
    - 所有工具调用与异常信息均通过 `logger` 进行记录。  
    - 使用自定义异常 `TokenLimitExceeded` 来捕获 token 数量超限的错误。  
    - 在工具调用错误或 JSON 解析错误时，返回对应的错误消息。  

  - **优化与功能改进建议**：  
    - 支持更多工具类型的自动注册与管理。  
    - 提供自定义工具调用策略的配置接口。  
    - 添加对异步工具调用的优化与并发处理。  


#### B. flow 子目录
- **\_\_init\_\_.py**  
  - 空文件，初始化用。

- **base.py**  
  - **主要功能**：  
    - 定义 `BaseFlow` 抽象基类，为支持多个代理的执行流程提供统一框架。  
    - 使用 `pydantic.BaseModel` 进行数据验证与管理，并继承自 `ABC` 以支持抽象方法定义。  
    - 支持多种形式的代理输入：单个代理、代理列表或代理字典。  
    - 提供 `execute()` 抽象方法，要求子类实现具体的流程执行逻辑。  

  - **主要组件与类**：  
    - `BaseFlow`：抽象基类，用于定义支持多个代理的执行流程。  
      - `agents`：包含所有代理的字典（`Dict[str, BaseAgent]`）。  
      - `tools`：可选的工具列表，默认为 `None`。  
      - `primary_agent_key`：主代理的键值，默认为 `None`。  
      - `Config`：允许自定义的类型 (`arbitrary_types_allowed = True`)。  
      - `__init__()`：支持代理的不同输入形式，并自动设置主代理的键。  
      - `primary_agent` 属性：获取当前流程的主代理。  
      - `get_agent()`：根据键名获取指定的代理。  
      - `add_agent()`：添加新的代理至流程中。  
      - `execute()` 抽象方法：要求子类实现具体的执行逻辑。  

  - **优化与功能改进建议**：  
    - 可以在 `execute()` 方法中引入日志记录功能，以便于流程调试与监控。  
    - 支持工具调用的动态配置与更新。  
    - 提供更多代理间通信的接口，支持代理协同工作。  

- **flow_factory.py**  
  - **主要功能**：  
    - 定义 `FlowFactory` 工厂类，用于创建不同类型的执行流程 (`BaseFlow` 的子类)。  
    - 引入 `FlowType` 枚举类，用于定义支持的流程类型（目前仅包含 `PLANNING` 类型）。  
    - 提供静态方法 `create_flow()` 用于创建并返回指定类型的流程实例。  

  - **主要组件与类**：  
    - `FlowType`：定义支持的流程类型的枚举类。  
      - 当前支持的类型：  
        - `PLANNING`：用于任务规划流程 (`PlanningFlow`)。  
    - `FlowFactory`：流程工厂类，提供创建不同流程实例的方法。  
      - `create_flow()`：静态方法，根据传入的 `flow_type` 和 `agents` 创建相应的流程实例。  
        - 参数：  
          - `flow_type` (`FlowType`)：指定要创建的流程类型。  
          - `agents` (`Union[BaseAgent, List[BaseAgent], Dict[str, BaseAgent]]`)：用于创建流程的代理实例或实例集合。  
          - `kwargs`：其他可选参数。  
        - 返回：指定类型的流程实例 (`BaseFlow` 的子类)。  
        - 异常处理：若传入的 `flow_type` 无法识别，则抛出 `ValueError`。  

  - **优化与功能改进建议**：  
    - 扩展 `FlowType` 枚举，支持更多类型的流程（例如 `SandboxFlow`, `MCPFlow` 等）。  
    - 提供流程注册机制，允许动态添加新的流程类型，而不必修改现有代码。  
    - 在 `create_flow()` 方法中引入日志记录，以便于流程创建的调试与监控。  

- **planning.py**  
  - **主要功能**：  
    - 定义 `PlanningFlow` 类，实现任务规划和执行流程的管理，支持多个代理的协作执行。  
    - 使用 `LLM` 和 `PlanningTool` 模块来自动生成和管理任务计划。  
    - 提供执行步骤的自动化流程，包括计划创建、步骤执行、状态更新和计划总结。  

  - **主要组件与类**：  
    - `PlanStepStatus`：枚举类，定义了可能的步骤状态。  
      - `NOT_STARTED`、`IN_PROGRESS`、`COMPLETED`、`BLOCKED`。  
      - 提供了状态列表 (`get_all_statuses()`)、活跃状态列表 (`get_active_statuses()`) 和状态标记 (`get_status_marks()`) 的静态方法。  
    - `PlanningFlow`：任务规划执行流程类，继承自 `BaseFlow`。  
      - `llm`：语言模型对象 (`LLM`)，用于与代理交互并生成计划。  
      - `planning_tool`：工具对象 (`PlanningTool`)，用于创建和管理任务计划。  
      - `executor_keys`：代理执行器键列表，用于选择适当的代理。  
      - `active_plan_id`：当前执行的计划 ID。  
      - `current_step_index`：当前执行的步骤索引。  

  - **主要方法与属性**：  
    - `get_executor()`：根据步骤类型返回相应的代理。  
    - `execute()`：执行整个规划流程，从创建初始计划到逐步完成所有任务。  
    - `_create_initial_plan()`：根据用户输入创建初始计划。  
    - `_get_current_step_info()`：从当前计划中获取需要执行的步骤信息。  
    - `_execute_step()`：执行当前步骤并记录执行结果。  
    - `_mark_step_completed()`：标记当前步骤为完成状态。  
    - `_get_plan_text()`：获取当前计划的文本表示。  
    - `_generate_plan_text_from_storage()`：从存储中生成计划的文本表示（用于备选方案）。  
    - `_finalize_plan()`：生成计划的总结信息。  

  - **优化与功能改进建议**：  
    - 提供不同类型的计划（如 `SandboxFlow`、`MCPFlow`）以支持更多任务。  
    - 增加对计划的并行执行支持，提高任务执行效率。  
    - 提供自定义的工具调用策略和代理选择规则。  
    - 在 `execute()` 流程中增加对错误的细粒度捕获与恢复机制。  


#### C. mcp 子目录
- **\_\_init\_\_.py**  
  - 空文件，初始化用。

- **server.py**  
  - **主要功能**：  
    - 实现 MCP 服务端，用于管理任务分发和多代理之间的通信。  
    - 提供了工具的注册与管理机制，并支持多种工具（如 `Bash`、`BrowserUseTool`、`StrReplaceEditor` 和 `Terminate`）的集成与调用。  
    - 提供清理功能，确保在服务器关闭或工具调用完成后释放资源。  
    - 支持通过 `FastMCP` 框架提供的 `tool()` 装饰器进行工具的注册与调用。  
    - 支持通过 `stdio` 作为通信方式进行数据传输。  

  - **主要组件与类**：  
    - `MCPServer`：MCP 服务器的核心实现类。  
      - `__init__()`：初始化服务器，加载并注册标准工具。  
      - `register_tool()`：注册单个工具至服务器，并生成相应的异步调用方法。  
      - `_build_docstring()`：生成工具的文档字符串，包含参数说明与用途。  
      - `_build_signature()`：生成工具的函数签名，用于验证调用参数。  
      - `register_all_tools()`：批量注册服务器内置的所有工具。  
      - `run()`：启动服务器，支持 `stdio` 传输方式。  
      - `cleanup()`：执行服务器资源清理，特别是 `BrowserUseTool` 的清理操作。  
      
    - `parse_args()`：用于解析命令行参数，目前支持 `--transport` 参数（默认为 `stdio`）。  

  - **主要工具集成**：  
    - `Bash`：用于执行系统命令的工具。  
    - `BrowserUseTool`：用于操作浏览器的工具，支持状态管理与资源清理。  
    - `StrReplaceEditor`：用于字符串替换与编辑的工具。  
    - `Terminate`：用于终止任务的工具。  

  - **调用示例**：  
    ```bash
    python server.py --transport stdio
    ```
    启动 MCP 服务器，使用 `stdio` 作为通信方式。  

  - **优化与功能改进建议**：  
    - 支持更多的工具注册机制（如自动扫描工具目录）。  
    - 增加对 `http` 传输方式的支持。  
    - 提供工具使用日志记录与调用统计。  

#### D. prompt 子目录
- **\_\_init\_\_.py**  
  - 空文件，初始化用。

- **browser.py**  
  - **主要功能**：  
    - 提供用于浏览器相关任务的系统提示模板 (`SYSTEM_PROMPT`) 和下一步提示模板 (`NEXT_STEP_PROMPT`)。  
    - 定义了浏览器任务的输入格式、响应规则、动作列表以及任务完成的标准。  
    - 指导代理如何在页面上进行交互，包括表单填写、内容提取、导航等。  
    - 提供了详细的规则与格式要求，确保代理在执行任务时保持一致性与准确性。  

  - **主要组件与变量**：  
    - `SYSTEM_PROMPT`：用于初始化代理的系统提示，提供所有任务的执行规范与格式要求。  
      - 包含输入格式、响应规则、动作序列、元素交互规则、导航与错误处理、任务完成标准等。  
      - 支持表单填写、内容提取、导航、错误处理与长任务的跟踪。  
      - 明确规定了代理在遇到不同情况（如 CAPTCHA、页面未加载完全等）时应采取的策略。  
      - 提供了统一的响应格式规范，确保所有交互行为以 JSON 格式输出。  
    - `NEXT_STEP_PROMPT`：用于指导代理在每一步操作完成后进行下一步决策。  
      - 提供了环境上下文信息占位符（如当前 URL、可用标签页、交互元素等）。  
      - 指导代理如何根据当前状态与已知信息进行下一步操作。  
      - 提供了一些常见的操作指令示例（如导航、点击、输入、提取内容、滚动等）。  
      - 强调了代理在执行过程中应保持对当前状态的记录与追踪。  

  - **优化与功能改进建议**：  
    - 添加更多交互场景的示例（如分页处理、数据爬取、自动化登录等）。  
    - 提供针对特定网站或应用的自定义系统提示模板。  
    - 支持不同类型的代理（如基于表单填写的代理、基于内容提取的代理）使用不同的系统提示模板。  
    - 增强对动态页面加载与异步请求的支持。  

- **cot.py**  
  - **主要功能**：  
    - 提供用于链式思考（Chain of Thought）任务的系统提示模板 (`SYSTEM_PROMPT`) 和下一步提示模板 (`NEXT_STEP_PROMPT`)。  
    - 指导代理以逐步推理的方式解决问题，包括问题分解、逐步推理、综合结论和最终回答。  
    - 强调思维过程的完整性与清晰性，以确保复杂问题能够被合理拆解与分析。  

  - **主要组件与变量**：  
    - `SYSTEM_PROMPT`：用于初始化代理的系统提示，提供链式思考任务的执行规范与格式要求。  
      - 包含四个步骤：  
        1. **问题分解**：将复杂问题拆解为更小、更易管理的部分。  
        2. **逐步推理**：对每个部分进行详细的思考与推理，并展示推理过程。  
        3. **综合结论**：将所有部分的思考结果综合成一个完整的解决方案。  
        4. **提供答案**：根据推理过程提供明确且简洁的答案。  
      - 明确要求响应格式为：  
        ```plaintext
        Thinking: [详细的思维过程，包含问题分解、每一步的推理与分析]
        Answer: [基于思维过程的最终答案，清晰且简洁]
        ```
      - 强调了思维过程的重要性，要求代理在回答时展示出完整的推理路径。  

    - `NEXT_STEP_PROMPT`：用于引导代理在每一步操作后继续推理或提供最终答案。  
      - 提示代理根据前面的对话内容继续进行推理。  
      - 如果已经得出结论，则提供最终的答案。  

  - **优化与功能改进建议**：  
    - 提供更加细化的思维模板，例如针对数学推理、逻辑推理或文本分析的专用提示。  
    - 引入步骤编号与结构化格式，以便于更加清晰地展示思维过程。  
    - 支持对复杂问题进行自动化分解与模块化处理。  


- **manus.py**  
  - **主要功能**：  
    - 提供用于 OpenManus 代理的系统提示模板 (`SYSTEM_PROMPT`) 和下一步提示模板 (`NEXT_STEP_PROMPT`)。  
    - 指导代理在处理复杂任务时，自主选择工具并以模块化的方式逐步完成任务。  
    - 支持多种工具调用，包括编程、信息检索、文件处理与网页浏览等。  

  - **主要组件与变量**：  
    - `SYSTEM_PROMPT`：用于初始化 OpenManus 代理的系统提示。  
      - 强调 OpenManus 作为通用的 AI 助手，具备解决用户提出的各种任务的能力。  
      - 提供多种工具调用的接口，并能够灵活组合使用。  
      - 提供了一个初始目录路径占位符 `{directory}`，用于指定当前的工作目录。  
      - 明确告知代理可以使用的工具范围，包括编程、信息检索、文件处理与网页浏览。  
      - 示例：  
        ```plaintext
        You are OpenManus, an all-capable AI assistant, aimed at solving any task presented by the user. You have various tools at your disposal that you can call upon to efficiently complete complex requests. Whether it's programming, information retrieval, file processing, or web browsing, you can handle it all.
        The initial directory is: {directory}
        ```  

    - `NEXT_STEP_PROMPT`：用于指导 OpenManus 在任务执行过程中选择最合适的工具或工具组合。  
      - 强调代理在面对复杂任务时，可以将问题拆解为多个步骤，并逐步调用工具来完成。  
      - 要求在每次工具调用后，清晰地解释执行结果，并提出下一步的建议。  
      - 鼓励代理根据用户需求灵活调整执行策略，并记录任务进展。  
      - 示例：  
        ```plaintext
        Based on user needs, proactively select the most appropriate tool or combination of tools. For complex tasks, you can break down the problem and use different tools step by step to solve it. After using each tool, clearly explain the execution results and suggest the next steps.
        ```  

  - **优化与功能改进建议**：  
    - 增加对不同工具调用的例子与说明，以便于更快适应新工具的使用。  
    - 提供针对不同任务类型（如文本分析、数据处理、网络交互）的自定义提示模板。  
    - 支持工具调用日志的自动记录与输出格式的标准化。  


- **mcp.py**  
  - **主要功能**：  
    - 提供用于 MCP 代理的系统提示模板 (`SYSTEM_PROMPT`)、下一步提示模板 (`NEXT_STEP_PROMPT`)、工具错误处理提示模板 (`TOOL_ERROR_PROMPT`) 和多媒体响应提示模板 (`MULTIMEDIA_RESPONSE_PROMPT`)。  
    - 指导 MCP 代理与 MCP 服务器交互，并根据提供的工具进行动态任务执行。  
    - 确保工具调用格式化正确，并能应对工具集动态变化的场景。  

  - **主要组件与变量**：  
    - `SYSTEM_PROMPT`：用于初始化 MCP 代理的系统提示。  
      - 强调 MCP 代理通过与 MCP 服务器通信来访问动态暴露的工具集。  
      - 提示代理在调用工具前，应当先检查可用工具列表。  
      - 提供了工具调用的标准流程：选择工具、提供参数、观察结果、判断下一步操作。  
      - 提醒代理工具集可能随时更新，应灵活应对新工具的出现或旧工具的消失。  
      - 指导代理在使用工具时，确保参数格式符合工具的定义，并在出错时优雅地处理与纠正。  
      - 强调工具调用过程中应逐步完成任务，并记录详细的执行过程与原因。  

    - `NEXT_STEP_PROMPT`：用于指导 MCP 代理在每一步操作后决定下一步的最佳工具调用。  
      - 要求代理结合当前状态与可用工具，分析下一步应该采取的操作。  
      - 鼓励代理在任务执行过程中，保持逻辑性与清晰性。  
      - 强调任务应按步骤完成，并记录每一步的进展。  

    - `TOOL_ERROR_PROMPT`：用于在工具调用出错时给出修正提示。  
      - 提醒代理检查参数格式、工具是否可用、操作是否被支持等。  
      - 提供了常见错误原因的列表，以帮助代理快速定位与修复问题。  

    - `MULTIMEDIA_RESPONSE_PROMPT`：用于处理来自工具的多媒体响应。  
      - 提醒代理使用描述信息来继续任务或为用户提供反馈。  
      - 确保多媒体内容能够被充分利用，而不是被忽略。  

  - **优化与功能改进建议**：  
    - 增加对工具调用状态的实时监控与日志记录。  
    - 提供标准化的工具调用格式与调用示例，以提高代理的执行效率。  
    - 支持对工具列表的自动刷新与动态更新。  
    - 引入更多工具类型（如图像处理、语音识别）并相应更新提示模板。  


- **planning.py**  
  - **主要功能**：  
    - 提供用于任务规划代理（Planning Agent）的系统提示模板 (`PLANNING_SYSTEM_PROMPT`) 和下一步提示模板 (`NEXT_STEP_PROMPT`)。  
    - 指导代理在处理复杂任务时，制定结构化的计划并高效地执行各个步骤。  
    - 支持任务的分解、步骤执行、进度追踪与任务完成的判断。  

  - **主要组件与变量**：  
    - `PLANNING_SYSTEM_PROMPT`：用于初始化 Planning Agent 的系统提示。  
      - 明确规划代理的职责：分析任务、制定计划、执行步骤、跟踪进度、完成任务。  
      - 提供五个核心步骤：  
        1. **任务分析**：理解任务的整体范围与目标。  
        2. **计划制定**：使用 `planning` 工具创建结构化的计划，确保每个步骤都能够推动任务向前。  
        3. **步骤执行**：根据计划依次调用工具完成各个步骤。  
        4. **进度追踪与调整**：根据任务进展动态更新计划。  
        5. **任务完成**：当任务完全完成时，使用 `finish` 工具结束任务。  
      - 列举了常用的工具：  
        - `planning`：用于创建、更新与跟踪计划，支持命令如 `create`、`update`、`mark_step` 等。  
        - `finish`：用于在任务完成后立即结束。  
      - 强调任务分解应当合理而简洁，避免过度细化或冗余的步骤。  
      - 指导代理在处理过程中要注意依赖关系与验证方法的使用。  
      - 要求在完成任务后立即调用 `finish`，避免不必要的冗余思考。  

    - `NEXT_STEP_PROMPT`：用于引导 Planning Agent 在任务执行过程中选择下一步操作。  
      - 提供了三个关键问题：  
        1. 计划是否足够完善？是否需要进一步优化或细化？  
        2. 当前步骤是否可以立即执行？  
        3. 任务是否已经完成？如果完成，则应立即调用 `finish`。  
      - 强调代理应在每一步操作前进行简洁明了的推理，并迅速采取合适的工具或行动。  

  - **优化与功能改进建议**：  
    - 提供对不同任务类型（如数据处理、文本生成、文件操作等）的专用提示模板。  
    - 增加针对任务复杂度的动态规划策略调整机制。  
    - 支持任务进度的自动化追踪与实时反馈。  
    - 提供计划模板或例子，帮助代理更快制定高效的执行计划。  

- **swe.py**  
  - **主要功能**：  
    - 提供用于软件工程代理（SWE Agent）的系统提示模板 (`SYSTEM_PROMPT`)。  
    - 指导代理在命令行环境中进行代码编辑与操作。  
    - 强调了工具调用格式的规范性与单步操作的原则。  

  - **主要组件与变量**：  
    - `SYSTEM_PROMPT`：用于初始化 SWE Agent 的系统提示。  
      - 设置场景 (`SETTING`)：代理在一个特殊的命令行界面中工作，并且能够通过工具调用进行文件编辑与操作。  
      - 特殊界面说明：  
        - 文件编辑器一次显示 `{{WINDOW}}` 行文件内容。  
        - 支持标准的 bash 命令与特定的工具调用（如编辑、导航等）。  
        - 工具调用必须以函数调用的形式进行。  
      - 提醒与规范：  
        - 编辑命令要求精确的缩进格式，否则将导致执行失败。  
        - 每次响应只能包含一个工具调用或函数调用，并且必须等待返回结果后才能继续。  
        - 禁止连续调用多个工具；代理应按步骤逐步完成任务。  
        - 不支持交互式会话命令（如 `python`、`vim` 等）。  
      - 响应格式：  
        - 每次调用的格式应包含当前打开的文件路径 (`<path>`) 与当前工作目录 (`<cwd>`)。  
        - 使用 `bash-$` 提示符表示命令行输入点。  
        - 在每次调用前应包含简短的思考过程说明。  
        - 强调了每次调用后应等待响应再继续操作。  
      - 示例格式：  
        ```plaintext
        (Open file: /path/to/file.py)
        (Current directory: /home/user/project)
        bash-$

        Thought: I will navigate to the desired file and then make the necessary edits.
        Tool Call: edit_file(file_path="/path/to/file.py", line_number=10, content="        print(x)")
        ```  

  - **优化与功能改进建议**：  
    - 提供对常用命令与工具调用的示例说明，以提高代理的操作效率。  
    - 引入任务记录与状态保存功能，确保长任务能够被中断后继续执行。  
    - 支持对常见错误（如缩进错误、文件不存在）的自动检测与纠正。  
    - 提供多文件编辑的工具调用策略与示例。  

- **toolcall.py**  
  - **主要功能**：  
    - 提供用于工具调用代理（ToolCall Agent）的系统提示模板 (`SYSTEM_PROMPT`) 和下一步提示模板 (`NEXT_STEP_PROMPT`)。  
    - 指导代理在处理任务时，通过工具调用来执行特定的操作。  
    - 提供简单而通用的工具调用接口，适用于各种工具的调用与管理。  

  - **主要组件与变量**：  
    - `SYSTEM_PROMPT`：用于初始化 ToolCall Agent 的系统提示。  
      - 简明直接地说明了代理的核心功能：执行工具调用。  
      - 不限制工具调用的类型或用途，使得代理可以灵活地调用不同的工具。  
      - 示例：  
        ```plaintext
        You are an agent that can execute tool calls
        ```  

    - `NEXT_STEP_PROMPT`：用于引导代理在任务执行过程中决定下一步操作。  
      - 提醒代理在需要停止交互时使用 `terminate` 工具或函数调用。  
      - 提供一个明确的终止方式，避免代理陷入无限循环或冗余操作。  
      - 示例：  
        ```plaintext
        If you want to stop interaction, use `terminate` tool/function call.
        ```  

  - **优化与功能改进建议**：  
    - 增加对不同工具调用方式的说明与示例，以提高代理的调用准确性。  
    - 提供对工具调用错误的自动检测与反馈机制。  
    - 支持多工具调用的链式执行与结果组合。  


#### E. sandbox 子目录
- **\_\_init\_\_.py**  
  - **主要功能**：  
    - 初始化沙箱模块，为 Docker 沙箱环境提供资源限制与隔离的安全执行环境。  
    - 提供了与沙箱相关的客户端接口、异常类型、管理器与核心沙箱实现的导入。  
    - 将所有核心组件通过 `__all__` 公开，便于外部模块导入与使用。  

  - **主要组件与导入内容**：  
    - `DockerSandbox`：核心沙箱类，实现基于 Docker 的安全执行环境。  
    - `SandboxManager`：用于管理多个沙箱实例的创建与销毁。  
    - `BaseSandboxClient`：沙箱客户端的基础接口类。  
    - `LocalSandboxClient`：本地沙箱客户端实现，支持在本地环境中运行 Docker 沙箱。  
    - `create_sandbox_client()`：用于动态创建沙箱客户端的工厂方法。  
    - `SandboxError`：通用沙箱错误类型。  
    - `SandboxResourceError`：资源限制相关的异常。  
    - `SandboxTimeoutError`：沙箱执行超时的异常。  

  - **公开接口 (`__all__`)**：  
    ```python
    __all__ = [
        "DockerSandbox",
        "SandboxManager",
        "BaseSandboxClient",
        "LocalSandboxClient",
        "create_sandbox_client",
        "SandboxError",
        "SandboxTimeoutError",
        "SandboxResourceError",
    ]
    ```  

#### E. sandbox 子目录
- **client.py**  
  - **主要功能**：  
    - 定义了沙箱客户端的接口、协议与本地实现 (`LocalSandboxClient`)，用于与 Docker 沙箱进行交互。  
    - 提供了创建、命令执行、文件传输与资源清理的功能接口。  
    - 实现了与 `DockerSandbox` 类的集成，通过异步接口提供安全的沙箱管理与执行环境。  

  - **主要组件与类**：  
    - `SandboxFileOperations (Protocol)`：定义了文件操作的协议，提供以下方法：  
      - `copy_from()`：从容器复制文件到本地。  
      - `copy_to()`：从本地复制文件到容器。  
      - `read_file()`：读取容器内文件的内容。  
      - `write_file()`：将内容写入容器内的文件。  
      
    - `BaseSandboxClient (ABC)`：抽象基类，定义了沙箱客户端的基础接口，提供以下方法：  
      - `create()`：创建沙箱。  
      - `run_command()`：在沙箱中执行命令。  
      - `copy_from()`：从沙箱中复制文件。  
      - `copy_to()`：复制文件到沙箱中。  
      - `read_file()`：读取文件。  
      - `write_file()`：写入文件。  
      - `cleanup()`：清理沙箱资源。  

    - `LocalSandboxClient (BaseSandboxClient)`：本地沙箱客户端的具体实现。  
      - 使用 `DockerSandbox` 类实现所有方法的具体逻辑。  
      - 提供对文件传输、命令执行与资源清理的支持。  
      - 所有方法均为异步方法，支持在协程环境中调用。  
      - 当 `cleanup()` 被调用时，将删除与沙箱相关的资源并重置状态。  
      
    - `create_sandbox_client()`：工厂函数，用于创建一个 `LocalSandboxClient` 实例。  
      - 返回：`LocalSandboxClient` 实例。  
      
    - `SANDBOX_CLIENT`：全局实例，提供统一的沙箱客户端接口。  

  - **优化与功能改进建议**：  
    - 支持更多类型的沙箱客户端（如远程沙箱或 Kubernetes 集群）。  
    - 提供更丰富的文件操作接口（如目录拷贝、文件压缩与解压缩）。  
    - 增强错误处理机制，提供更加详细的异常信息。  
    - 在 `create()` 方法中支持更多配置参数与资源限制选项。  

- **core/**  
  - **exceptions.py**  
    - **主要功能**：  
      定义了沙箱系统中可能抛出的自定义异常，以便于在不同组件中进行统一的错误处理和响应。  

    - **核心异常类**：  
      - `SandboxError`：基础异常类，所有与沙箱系统相关的错误都应继承自该类。  
      - `SandboxTimeoutError`：在沙箱操作超过指定的超时时间时抛出。  
      - `SandboxResourceError`：当沙箱资源（如内存、CPU 等）不足或配置不当时抛出。  

    - **用途与作用**：  
      提供了一个标准的异常层次结构，确保不同模块中的错误处理方式保持一致。  
 
  - **manager.py**  
    - **主要功能**：  
      实现 `SandboxManager` 类，用于管理多个 Docker 沙箱 (`DockerSandbox`) 的生命周期，包括创建、监控、清理等功能。  

    - **核心组件与类**：  
      - `SandboxManager`：  
        - 管理多个沙箱实例，并提供并发访问控制与自动清理机制。  
        - 支持按需创建沙箱 (`create_sandbox`)、获取沙箱 (`get_sandbox`)、删除沙箱 (`delete_sandbox`) 以及全局清理 (`cleanup`)。  
        - 提供沙箱资源的自动清理任务 (`start_cleanup_task`)。  
        - 提供沙箱并发访问控制与资源限制的管理。  

    - **主要方法**：  
      - `create_sandbox()`：创建新的沙箱实例并返回其 ID。  
      - `get_sandbox()`：根据沙箱 ID 返回对应的沙箱实例。  
      - `delete_sandbox()`：删除指定的沙箱。  
      - `cleanup()`：清理所有资源并终止所有沙箱。  
      - `start_cleanup_task()`：启动自动清理任务的后台进程。  
      - `_cleanup_idle_sandboxes()`：定期检查并清理长时间未使用的沙箱。  

    - **日志与异常处理**：  
      - 所有操作均通过 `logger` 记录。  
      - 对 Docker API 错误与异步操作错误进行了统一捕捉与处理。  

    - **用途与作用**：  
      提供一个集中化的沙箱管理系统，确保资源的高效利用与安全性。

  - **sandbox.py**  
    - **主要功能**：  
      实现 `DockerSandbox` 类，提供一个基于 Docker 的沙箱环境，支持命令执行、文件操作和资源管理。  

    - **核心组件与类**：  
      - `DockerSandbox`：  
        - 提供容器化的执行环境，支持自定义的配置（如内存限制、CPU 限制、网络设置等）。  
        - 支持文件的读取、写入、拷贝操作以及命令执行。  
        - 提供安全的路径解析与权限管理。  
        - 支持异步的容器创建、命令执行与资源清理。  

    - **主要方法**：  
      - `create()`：创建并启动 Docker 容器。  
      - `run_command()`：在容器内执行指定命令。  
      - `read_file()` / `write_file()`：提供文件的读写操作。  
      - `copy_from()` / `copy_to()`：支持文件在主机与容器之间的复制。  
      - `_prepare_volume_bindings()`：配置容器的卷挂载映射。  
      - `_safe_resolve_path()`：确保路径安全性，防止路径遍历攻击。  
      - `cleanup()`：终止容器并释放资源。  

    - **日志与异常处理**：  
      - 针对 Docker API 的调用错误进行了统一捕捉与处理。  
      - 提供详细的错误信息与资源清理功能。  

    - **用途与作用**：  
      提供一个安全、高效的 Docker 容器管理接口，适用于需要隔离执行的任务或环境。  

  - **terminal.py**  
    - **主要功能**：  
      提供 `AsyncDockerizedTerminal` 类，用于与 Docker 容器交互的异步终端系统，支持命令执行与结果读取。  

    - **核心组件与类**：  
      - `DockerSession`：提供与容器的底层交互接口。  
        - 支持异步的命令执行与输入输出流管理。  
        - 提供 `create()`、`close()` 与 `execute()` 方法管理容器内的终端会话。  
      - `AsyncDockerizedTerminal`：高级封装接口，用于异步执行容器内命令并处理返回结果。  
        - 支持文件操作与环境变量的设置。  
        - 提供异步上下文管理 (`__aenter__()` / `__aexit__()`) 以自动管理会话的生命周期。  

    - **主要方法**：  
      - `run_command()`：在容器内运行命令，并捕捉输出。  
      - `_exec_simple()`：用于执行简单命令，并获取结果。  
      - `init()`：初始化 Docker 会话与终端环境。  
      - `close()`：清理终端资源并关闭会话。  

    - **异常处理与安全性**：  
      - 提供了命令注入检查与异常处理。  
      - 对潜在危险命令进行拦截与过滤。  

    - **用途与作用**：  
      提供与 Docker 容器的异步交互功能，允许高效、安全地执行容器内的任务。  

#### F. tool 子目录
  - **\_\_init\_\_.py**  
    - **主要功能**：  
      初始化 `tool` 模块，导入并统一管理所有工具类与接口，以便于在 OpenManus 系统中进行统一的调用和注册。  

    - **导入的工具模块**：  
      - `BaseTool`：所有工具的抽象基类，定义了工具的核心接口与行为。  
      - `Bash`：用于在沙箱环境中执行系统命令的工具。  
      - `BrowserUseTool`：提供与浏览器交互的工具（如自动化浏览器操作、网页抓取等）。  
      - `CreateChatCompletion`：用于与 LLM 进行聊天补全的工具接口。  
      - `DeepResearch`：实现深入调研或复杂信息分析的工具。  
      - `PlanningTool`：用于任务规划与步骤管理的工具。  
      - `StrReplaceEditor`：提供字符串替换或编辑的工具。  
      - `Terminate`：用于安全终止任务或进程的工具。  
      - `ToolCollection`：将多个工具组合在一起，便于统一管理与调用。  
      - `WebSearch`：提供基于搜索引擎（如 Google、Bing 等）的网络搜索工具。  

    - **核心组件与接口定义**：  
      - `__all__` 列表：用于显式声明模块的公开接口，包含所有已定义的工具类。  

    - **用途与作用**：  
      - 提供统一的接口与工具调用管理层，使得 OpenManus 系统能够灵活、规范地调用不同的工具。  
      - 所有工具类均继承自 `BaseTool`，并实现各自的功能。  

  - **base.py**  
    - **主要功能**：  
      定义了所有工具的基础抽象类 `BaseTool`，以及工具执行结果的标准数据结构 `ToolResult` 和其扩展类。  
      提供了一个通用的工具调用接口，所有具体工具均继承自 `BaseTool` 并实现其抽象方法。  

    - **核心组件与类**：  
      - `BaseTool`（抽象基类）：  
        - 所有工具的基础接口，定义了工具的名称、描述、参数与执行方式。  
        - 必须实现的抽象方法：`execute()`。  
        - 提供了标准的工具调用格式转换接口：`to_param()`。  
        - 支持异步调用，通过 `__call__()` 方法统一调用方式。  
      
      - `ToolResult`：  
        - 表示工具执行结果的数据结构，继承自 `BaseModel`。  
        - 包含四个字段：  
          - `output`：工具执行的返回值。  
          - `error`：如果执行中发生错误，则记录错误信息。  
          - `base64_image`：如果返回内容包含图片，则存储为 Base64 编码字符串。  
          - `system`：工具运行时的系统信息或状态。  
        - 提供 `__bool__()` 和 `__add__()` 方法，支持布尔判断与结果合并操作。  
        - 支持通过 `replace()` 方法修改任意字段并返回新的 `ToolResult` 实例。  

      - `CLIResult`：  
        - `ToolResult` 的子类，表示可以被渲染为命令行输出的工具结果。  

      - `ToolFailure`：  
        - `ToolResult` 的子类，表示工具执行失败时的结果。  

    - **用途与作用**：  
      - 所有工具类均应继承自 `BaseTool` 并实现 `execute()` 方法。  
      - 提供统一的工具执行结果格式，使得不同工具的结果可以以相同的接口进行处理与展示。  
      - 支持工具之间的结果合并与结果状态判断。  

  - **bash.py**  
    - **主要功能**：  
      提供一个用于执行 Bash 命令的工具 `Bash`，支持异步执行、命令输出读取、错误处理以及命令超时机制。  
      定义了一个 `Bash` 工具类和一个 `_BashSession` 类，用于处理 Bash 命令的执行会话与输出管理。  

    - **核心组件与类**：  
      - `_BashSession`（内部类）：  
        - 用于管理单次 Bash 会话。  
        - 支持命令的异步执行与输出读取，通过 `asyncio` 库实现。  
        - 提供 `start()`、`stop()`、`run()` 等方法。  
        - 支持自定义超时时间 `_timeout` 和输出读取延迟 `_output_delay`。  
        - 提供命令输出的结束标识符 `_sentinel`，用于判断命令是否执行完成。  
        - 支持在命令执行超时时抛出 `ToolError` 异常。  
      
      - `Bash`（工具类）：  
        - 继承自 `BaseTool`，实现了通用工具接口 `execute()`。  
        - 用于管理多个 `_BashSession` 实例，并处理命令执行与错误处理。  
        - 提供支持命令重启的机制 (`restart` 参数)，用于在会话出错或命令卡死时进行重启。  
        - 提供标准化的参数结构 `parameters`，定义了支持的命令格式与描述信息。  
        - 返回 `CLIResult` 对象作为执行结果，包含输出与错误信息。  

    - **工具调用参数定义 (`parameters`)**：  
      ```python
      parameters = {
          "type": "object",
          "properties": {
              "command": {
                  "type": "string",
                  "description": "The bash command to execute. Can be empty to view additional logs when previous exit code is `-1`. Can be `ctrl+c` to interrupt the currently running process.",
              },
          },
          "required": ["command"],
      }
      ```

    - **工具执行说明 (`Bash.execute()`)**：  
      - 当调用 `execute()` 时，如果 `restart=True`，则重启当前会话。  
      - 当提供 `command` 时，将尝试在当前 `_BashSession` 上执行该命令。  
      - 如果 `_BashSession` 尚未初始化，会自动创建新的会话。  
      - 命令执行的结果将返回 `CLIResult` 对象。  

    - **示例调用 (`__main__` 测试块)**：  
      ```python
      if __name__ == "__main__":
          bash = Bash()
          rst = asyncio.run(bash.execute("ls -l"))
          print(rst)
      ```

    - **用途与作用**：  
      - 提供与系统终端进行交互的工具，可以执行各种 Bash 命令。  
      - 用于文件管理、目录操作、程序启动等任务。  
      - 支持长时间运行的进程与后台命令的管理。  

  - **browser_use_tool.py**  
    - **主要功能**：  
      提供一个用于自动化 Web 浏览器操作的工具 `BrowserUseTool`，支持网页导航、交互、内容提取以及多标签页管理等功能。与前面的 `bash` 工具不同，它用于操作一个无头浏览器，通过 `browser_use` 库与网页内容进行交互。  

    - **核心组件与类**：  
      - `BrowserUseTool`（工具类）：  
        - 继承自 `BaseTool` 并实现了通用工具接口 `execute()`。  
        - 提供对浏览器的全面控制，包括导航、交互、内容提取等。  
        - 提供标准化的参数结构 `parameters`，定义了支持的操作与其参数。  
        - 返回 `ToolResult` 对象作为执行结果。  
        - 支持通过 `asyncio.Lock` 保证多线程调用的安全性。  
        - 支持与 Web 浏览器的会话保持与清理 (`cleanup()`)。  

      - `_ensure_browser_initialized()` 方法：  
        - 确保浏览器和上下文 (`BrowserContext`) 已被初始化。  
        - 根据 `config` 配置初始化浏览器并创建新的上下文。  
        - 如果提供了代理设置，则支持配置代理。  

      - `get_current_state()` 方法：  
        - 获取当前浏览器状态，包括：  
          - 当前的 URL、标题、标签页列表。  
          - 可交互元素列表与滚动信息。  
          - 当前网页的截图（以 base64 编码返回）。  

      - `cleanup()` 方法：  
        - 用于清理浏览器资源，关闭上下文与浏览器实例。  
        - 支持在工具对象被销毁时自动调用。  

      - `create_with_context()` 方法：  
        - 工厂方法，用于创建包含特定上下文的 `BrowserUseTool` 实例。  

    - **工具调用参数定义 (`parameters`)**：  
      ```python
      parameters = {
          "type": "object",
          "properties": {
              "action": {
                  "type": "string",
                  "enum": [
                      "go_to_url", "click_element", "input_text", "scroll_down", "scroll_up",
                      "scroll_to_text", "send_keys", "get_dropdown_options", "select_dropdown_option",
                      "go_back", "web_search", "wait", "extract_content", "switch_tab",
                      "open_tab", "close_tab"
                  ],
                  "description": "The browser action to perform",
              },
              "url": {"type": "string", "description": "URL for navigation or new tab"},
              "index": {"type": "integer", "description": "Element index for various interactions"},
              "text": {"type": "string", "description": "Text for input or search"},
              "scroll_amount": {"type": "integer", "description": "Pixels to scroll"},
              "tab_id": {"type": "integer", "description": "Tab ID for switching tabs"},
              "query": {"type": "string", "description": "Search query for web search"},
              "goal": {"type": "string", "description": "Goal for content extraction"},
              "keys": {"type": "string", "description": "Keys to send for keyboard actions"},
              "seconds": {"type": "integer", "description": "Seconds to wait for 'wait' action"}
          },
          "required": ["action"],
      }
      ```

    - **支持的浏览器操作 (`action`)**：  
      1. **页面导航**：  
         - `go_to_url`：打开指定 URL。  
         - `go_back`：返回上一个页面。  
         - `refresh`：刷新当前页面。  
         - `open_tab`：打开新的标签页。  
         - `close_tab`：关闭当前标签页。  
      
      2. **页面交互**：  
         - `click_element`：点击指定的元素。  
         - `input_text`：向指定元素输入文本。  
         - `send_keys`：发送键盘事件。  
         - `scroll_down` / `scroll_up`：上下滚动页面。  
         - `scroll_to_text`：滚动至特定文本。  
         - `get_dropdown_options` / `select_dropdown_option`：操作下拉菜单。  
      
      3. **内容提取与搜索**：  
         - `extract_content`：从页面提取信息，支持自定义提取目标 (`goal`)。  
         - `web_search`：通过搜索引擎查找内容并导航到结果页面。  
      
      4. **标签页管理**：  
         - `switch_tab`：切换到指定标签页。  

      5. **等待操作**：  
         - `wait`：等待指定秒数。  

    - **示例调用**：  
      ```python
      tool = BrowserUseTool()
      result = await tool.execute(action="go_to_url", url="https://example.com")
      print(result.output)
      ```

    - **用途与作用**：  
      - 用于自动化地与网页进行交互，如表单填写、内容抓取、自动登录等。  
      - 支持对不同浏览器标签页的管理与内容提取。  
      - 提供对网页元素的精细操作与提取控制。  

  - **create_chat_completion.py**  
    - **主要功能**：  
      提供一个用于生成结构化的聊天回复的工具 `CreateChatCompletion`。可以支持不同的数据类型（字符串、列表、字典、自定义模型等）的输出格式，并自动构建对应的 JSON Schema 参数。  

    - **核心组件与类**：  
      - `CreateChatCompletion`（工具类）：  
        - 继承自 `BaseTool` 并实现了通用工具接口 `execute()`。  
        - 提供了通过 `response_type` 参数自定义输出格式的功能。  
        - 自动根据 `response_type` 构建 JSON Schema 以用于验证与格式化。  
        - 提供了类型映射与类型检测功能以支持复杂的数据结构。  

      - `type_mapping`：  
        一个 Python 基本类型到 JSON Schema 类型的映射字典，例如：  
        ```python
        type_mapping = {
            str: "string",
            int: "integer",
            float: "number",
            bool: "boolean",
            dict: "object",
            list: "array",
        }
        ```
      
      - `response_type`：  
        用于定义返回的数据类型，可以是 Python 原生类型、Pydantic 模型、列表、字典，甚至是联合类型（`Union`）。  
      
      - `parameters`：  
        根据 `response_type` 自动生成的 JSON Schema。  

    - **核心方法**：  
      - `__init__(self, response_type: Optional[Type] = str)`：  
        初始化工具，并设置默认的 `response_type`。构建参数 schema。  

      - `_build_parameters()`：  
        根据 `response_type` 生成参数的 JSON Schema。如果是字符串类型，则简单生成；如果是 `BaseModel` 子类，则使用 Pydantic 提供的 `model_json_schema()` 生成；否则，调用 `_create_type_schema()`。  

      - `_create_type_schema(self, type_hint: Type)`：  
        根据提供的类型提示 (`type_hint`) 生成相应的 JSON Schema。支持以下类型：  
          - 原生类型：`str`, `int`, `float`, `bool` 等。  
          - 列表：例如 `List[str]`。  
          - 字典：例如 `Dict[str, int]`。  
          - 联合类型：`Union[str, int]`。  

      - `_create_union_schema(self, types: tuple)`：  
        用于处理联合类型 (`Union[...]`) 的 JSON Schema 生成。  

      - `_get_type_info(self, type_hint: Type)`：  
        将给定的类型提示转换为 JSON Schema 属性信息。  

      - `execute(self, required: list | None = None, **kwargs) -> Any`：  
        执行工具并返回符合 `response_type` 类型的输出。支持对返回数据进行类型转换与验证。  

    - **示例调用**：  
      ```python
      from typing import List, Union
      from pydantic import BaseModel
      
      class UserInfo(BaseModel):
          name: str
          age: int
      
      # 单个字符串返回
      tool = CreateChatCompletion(response_type=str)
      result = await tool.execute(response="Hello, World!")
      print(result)  # Output: "Hello, World!"
      
      # 返回列表
      tool = CreateChatCompletion(response_type=List[str])
      result = await tool.execute(response=["Hello", "World"])
      print(result)  # Output: ["Hello", "World"]
      
      # 返回自定义 Pydantic 模型
      tool = CreateChatCompletion(response_type=UserInfo)
      result = await tool.execute(name="Alice", age=30)
      print(result)  # Output: UserInfo(name="Alice", age=30)
      
      # 返回联合类型
      tool = CreateChatCompletion(response_type=Union[str, int])
      result = await tool.execute(response="Hello")
      print(result)  # Output: "Hello"
      ```
    
    - **用途与作用**：  
      - 用于生成结构化的聊天回复，例如 JSON 格式或自定义模型格式。  
      - 可以在与 LLM 集成时，确保生成的内容符合指定的数据类型。  
      - 灵活支持多种数据类型与复杂结构的响应格式。  

  - **deep_research.py**  
    - **主要功能**：  
      提供一个深入研究工具 `DeepResearch`，支持通过多层次的网络搜索、内容分析和结构化信息提取来完成复杂的研究任务。工具能从多个来源提取关键洞见，并基于已有发现生成新的研究方向。  

    - **核心组件与类**：  
      - `DeepResearch`（工具类）：  
        - 继承自 `BaseTool` 并实现了通用工具接口 `execute()`。  
        - 提供了一套流程化的研究方法，包括查询优化、网络搜索、洞见提取、以及后续研究问题生成。  
        - 可以递归地进行深度搜索，通过多轮搜索逐步收集更多的信息。  

      - `ResearchContext`：  
        用于跟踪当前的研究状态，包括查询、已发现的洞见、后续查询、已访问的 URL 列表，以及当前的深度。  

      - `ResearchInsight`：  
        用于存储每一个提取出的洞见，包括内容、来源 URL、标题、以及相关性评分。  

      - `ResearchSummary`：  
        用于总结所有研究过程中的结果，包括查询、洞见列表、访问的 URL 和最终达到的深度。  

    - **核心方法**：  
      - `execute()`：  
        执行主要的研究流程，包括：  
        1. **查询优化**：调用 LLM 对用户的原始查询进行优化，以获得更精确的搜索结果。  
        2. **构建研究图**：通过递归搜索与分析，逐步获取深层次的洞见。  
        3. **总结输出**：将所有的洞见与相关信息打包为 `ResearchSummary` 对象返回。  

      - `_generate_optimized_query()`：  
        使用 LLM 对原始查询进行优化，提供更有效的搜索关键词。  

      - `_research_graph()`：  
        递归执行搜索与分析任务，支持多个深度的探索。  

      - `_search_web()`：  
        执行 Web 搜索，并返回 `SearchResult` 对象列表。  

      - `_extract_insights()`：  
        从网络搜索的结果中提取洞见，并将它们存储在 `ResearchContext` 中。  

      - `_generate_follow_ups()`：  
        基于已提取的洞见生成新的研究问题，以扩展与深入当前的研究方向。  

      - `_analyze_content()`：  
        使用 LLM 对指定内容进行分析，并提取出与查询相关的关键洞见。  

    - **使用的 Prompt 模板**：  
      - `OPTIMIZE_QUERY_PROMPT`：用于优化用户输入的查询。  
      - `EXTRACT_INSIGHTS_PROMPT`：用于从内容中提取关键洞见。  
      - `GENERATE_FOLLOW_UPS_PROMPT`：用于生成新的研究问题。  

    - **输入参数与依赖关系**：  
      - `query`：必填参数，表示需要研究的主题或问题。  
      - `max_depth`：可选参数，定义递归研究的最大深度。  
      - `results_per_search`：每次搜索要获取的搜索结果数量。  
      - `max_insights`：返回的最大洞见数量。  
      - `time_limit_seconds`：设置任务的最大执行时间。  

    - **示例调用**：  
      ```python
      if __name__ == "__main__":
          deep_research = DeepResearch()
          result = asyncio.run(
              deep_research.execute(
                  query="What is deep learning", 
                  max_depth=1, 
                  results_per_search=2
              )
          )
          print(result)
      ```
    
    - **用途与作用**：  
      - 执行深入的互联网研究，例如：技术分析、市场研究、科学发现等。  
      - 提取结构化的信息并自动生成后续研究方向，提升研究效率。  
      - 提供多轮搜索与分析，以加深对某一主题的理解。  

  - **file_operators.py**  
    - **主要功能**：  
      提供了在本地与沙箱环境中进行文件操作的接口与实现。支持文件的读写操作、路径检查、以及执行命令等功能。提供了一种通用协议接口 `FileOperator` 以及两个实现类 `LocalFileOperator` 与 `SandboxFileOperator`。  

    - **核心组件与类**：  
      - **接口协议类 `FileOperator`**：  
        定义了文件操作的通用接口，支持以下方法：  
        - `read_file()`：从文件中读取内容。  
        - `write_file()`：将内容写入到文件。  
        - `is_directory()`：判断路径是否为目录。  
        - `exists()`：检查路径是否存在。  
        - `run_command()`：执行 shell 命令并返回结果。  

      - **`LocalFileOperator` 类**：  
        用于本地文件系统的操作。  
        - 实现了所有 `FileOperator` 接口中的方法。  
        - 使用标准的 `Pathlib` 库进行文件与路径操作。  
        - 使用 `asyncio.create_subprocess_shell()` 进行异步命令执行。  

      - **`SandboxFileOperator` 类**：  
        用于在沙箱环境中进行文件操作。  
        - 实现了所有 `FileOperator` 接口中的方法。  
        - 与 `SANDBOX_CLIENT` 配合使用，用于与沙箱进行通信与操作。  
        - 包含 `_ensure_sandbox_initialized()` 方法来确保沙箱环境已初始化。  
        - 在沙箱中运行命令时，返回代码总是 `0`，因为当前沙箱实现不提供具体的退出码。  

    - **输入参数与依赖关系**：  
      - `PathLike`：支持 `str` 或 `Path` 类型的路径。  
      - `cmd`：命令字符串。  
      - `timeout`：命令执行的超时时间（秒）。  

    - **主要方法与功能**：  
      - `LocalFileOperator.read_file()`：读取本地文件内容。  
      - `LocalFileOperator.write_file()`：将内容写入本地文件。  
      - `LocalFileOperator.is_directory()`：判断给定路径是否为目录。  
      - `LocalFileOperator.exists()`：判断给定路径是否存在。  
      - `LocalFileOperator.run_command()`：在本地运行命令并捕获输出与错误信息。  
      - `SandboxFileOperator.read_file()`：读取沙箱内文件内容。  
      - `SandboxFileOperator.write_file()`：将内容写入沙箱内文件。  
      - `SandboxFileOperator.is_directory()`：判断沙箱内路径是否为目录。  
      - `SandboxFileOperator.exists()`：判断沙箱内路径是否存在。  
      - `SandboxFileOperator.run_command()`：在沙箱内运行命令并捕获输出。  

    - **设计考量与区别**：  
      - `LocalFileOperator` 与 `SandboxFileOperator` 实现了相同的接口，因此可以在不同环境下自由替换。  
      - `SandboxFileOperator` 强调了沙箱的隔离性，确保所有操作在受控环境中进行。  
      - 由于沙箱执行的命令不会返回明确的退出码，所以统一返回 `0`。  

    - **使用场景**：  
      - `LocalFileOperator`：用于标准的本地文件操作，例如读取配置文件、保存日志文件等。  
      - `SandboxFileOperator`：用于在受控环境中进行文件处理，保证操作的安全性与隔离性。  

    - **示例调用**：  
      ```python
      local_operator = LocalFileOperator()
      result = asyncio.run(local_operator.read_file("example.txt"))
      print(result)
      
      sandbox_operator = SandboxFileOperator()
      result = asyncio.run(sandbox_operator.write_file("/sandbox/example.txt", "Hello, sandbox!"))
      print(result)
      ```

    - **改进建议**：  
      - 在 `SandboxFileOperator` 中添加命令执行的退出码捕获功能，以便更好地检测命令执行的状态。  
      - 增加对二进制文件的读写支持，而不仅仅是文本文件。  
      - 增加对文件权限与属性修改的支持。  

  - **mcp.py**  
    - **主要功能**：  
      提供了一套用于与 MCP (Model Context Protocol) 服务器交互的工具集合。支持通过 `SSE` 或 `Stdio` 方式连接服务器，检索可用工具并进行远程调用。实现了一个通用工具集合 `MCPClients` 和具体工具接口 `MCPClientTool`。  

    - **核心组件与类**：  
      - **`MCPClientTool` 类**：  
        - 用于封装一个可通过 MCP 协议远程调用的工具。  
        - 继承自 `BaseTool` 类。  
        - 属性：  
          - `session`：与 MCP 服务器的会话对象 `ClientSession`。  
        - 方法：  
          - `execute()`：调用远程工具并返回工具执行的结果。  
          - 异常处理：如果调用失败，返回 `ToolResult` 中包含错误信息。  

      - **`MCPClients` 类（工具集合）**：  
        - 用于管理所有通过 MCP 协议连接的工具。  
        - 继承自 `ToolCollection` 类。  
        - 属性：  
          - `session`：与 MCP 服务器的会话对象。  
          - `exit_stack`：用于管理异步资源清理的上下文栈。  
          - `tool_map`：一个字典，用于存储所有从 MCP 服务器加载的工具。  
        - 方法：  
          - `connect_sse()`：通过 `SSE` 协议连接 MCP 服务器。  
          - `connect_stdio()`：通过 `Stdio` 协议连接 MCP 服务器。  
          - `_initialize_and_list_tools()`：初始化会话，并从服务器检索工具列表。  
          - `disconnect()`：关闭当前会话并清理资源。  

    - **输入参数与依赖关系**：  
      - `server_url`：用于 `SSE` 连接时提供的服务器 URL。  
      - `command` 与 `args`：用于 `Stdio` 连接时提供的服务器命令与参数。  
      - `kwargs`：用于远程调用时提供的工具参数。  
      - 依赖库：`mcp`, `mcp.client.sse`, `mcp.client.stdio`。  

    - **主要方法与功能**：  
      - `MCPClientTool.execute()`：调用 MCP 服务器提供的工具。  
      - `MCPClients.connect_sse()`：建立基于 `SSE` 的连接。  
      - `MCPClients.connect_stdio()`：建立基于 `Stdio` 的连接。  
      - `MCPClients._initialize_and_list_tools()`：从 MCP 服务器检索工具列表，并实例化为 `MCPClientTool` 对象。  
      - `MCPClients.disconnect()`：断开与 MCP 服务器的连接并清理资源。  

    - **设计考量与特点**：  
      - `MCPClientTool` 与 `MCPClients` 相互配合，一个用于处理单个工具的调用，另一个用于管理多个工具的加载与调用。  
      - 支持异步调用与资源清理，通过 `AsyncExitStack` 提供优雅的资源管理。  
      - 提供了两种连接方式：`SSE` 和 `Stdio`，增强了与 MCP 服务器的通信灵活性。  
      - 自动化工具注册：工具通过 `_initialize_and_list_tools()` 方法动态加载并注册。  
      - 异常捕捉与日志记录：在工具调用或连接异常时，记录详细错误信息，便于调试。  

    - **使用场景**：  
      - 用于连接到 MCP 服务器，并与其提供的各种工具进行交互。  
      - 提供统一接口用于远程调用，支持灵活的工具参数传递与返回结果处理。  

    - **示例调用**：  
      ```python
      import asyncio
      from app.tool.mcp import MCPClients

      async def main():
          mcp_client = MCPClients()

          # 连接到 MCP 服务器（SSE）
          await mcp_client.connect_sse("http://localhost:8000")

          # 检索可用工具并调用其中一个
          tool = mcp_client.tool_map.get("example_tool")
          if tool:
              result = await tool.execute(param1="value1", param2="value2")
              print(result.output)
          
          # 断开连接
          await mcp_client.disconnect()

      asyncio.run(main())
      ```

    - **改进建议**：  
      - 支持对工具的参数验证与格式化，以增强输入的安全性与正确性。  
      - 增加对工具执行超时与重试机制的支持。  
      - 提供更多的日志输出配置选项以支持更详细的调试信息。  
      - 支持工具的批量调用与并行化执行，提高工具调用效率。  

  - **planning.py**  
    - **主要功能**：  
      提供一个用于创建、管理和跟踪复杂任务计划的工具。支持创建新的计划、更新步骤、标记步骤状态、列出计划、设置活动计划、删除计划等操作。  

    - **核心组件与类**：  
      - **`PlanningTool` 类**：  
        - 继承自 `BaseTool`。  
        - 提供了一个统一的接口来处理各种计划相关操作。  
        - 所有计划存储在类属性 `plans` 字典中，每个计划由唯一的 `plan_id` 标识。  
        - 属性：  
          - `name`：工具名称，默认为 `"planning"`。  
          - `description`：工具描述，包括支持的命令类型。  
          - `parameters`：支持的输入参数格式与验证规则。  
          - `plans`：所有计划的存储字典，格式为 `{plan_id: plan_data}`。  
          - `_current_plan_id`：当前活动的计划 ID。  

    - **支持的命令与方法**：  
      - `create`：创建一个新计划。  
        - 必需参数：`plan_id`, `title`, `steps`。  
        - 初始化步骤状态为 `not_started`。  
      - `update`：更新现有计划的标题或步骤。  
        - 必需参数：`plan_id`。  
        - 可选参数：`title`, `steps`。  
      - `list`：列出所有计划的概述，包括其标题、进度与活动状态。  
      - `get`：获取一个特定计划的详细信息。  
        - 可选参数：`plan_id`（若不提供则使用当前活动的计划）。  
      - `set_active`：将指定计划设置为活动状态。  
        - 必需参数：`plan_id`。  
      - `mark_step`：标记某个步骤的状态或附加注释。  
        - 必需参数：`step_index`, `step_status`。  
        - 可选参数：`step_notes`。  
      - `delete`：删除指定的计划。  
        - 必需参数：`plan_id`。  

    - **数据结构设计**：  
      每个计划存储为一个字典，包含以下字段：  
      ```python
      plan = {
          "plan_id": "unique_id",
          "title": "Plan Title",
          "steps": ["Step 1", "Step 2", "Step 3"],
          "step_statuses": ["not_started", "not_started", "not_started"],
          "step_notes": ["", "", ""]
      }
      ```
      - `steps`：任务步骤列表。  
      - `step_statuses`：与步骤列表一一对应的状态列表。  
      - `step_notes`：每个步骤对应的备注信息列表。  

    - **设计特点**：  
      - **灵活的命令系统**：支持多种命令，并允许通过参数来定制操作。  
      - **状态跟踪**：提供步骤的状态跟踪 (`not_started`, `in_progress`, `completed`, `blocked`)。  
      - **动态更新**：支持在已有计划中动态添加、修改或移除步骤。  
      - **自动保存活动计划**：当用户创建或修改计划时，自动更新为活动计划。  
      - **输出格式优化**：对每个操作返回的结果格式化，便于展示与查看。  

    - **示例调用**：  
      ```python
      import asyncio
      from app.tool.planning import PlanningTool

      async def main():
          planner = PlanningTool()
          
          # 创建一个新计划
          result = await planner.execute(
              command="create",
              plan_id="plan1",
              title="My First Plan",
              steps=["Step 1", "Step 2", "Step 3"]
          )
          print(result.output)
          
          # 列出所有计划
          result = await planner.execute(command="list")
          print(result.output)
          
          # 获取特定计划的详细信息
          result = await planner.execute(command="get", plan_id="plan1")
          print(result.output)
          
          # 标记步骤 0 为完成状态
          result = await planner.execute(command="mark_step", plan_id="plan1", step_index=0, step_status="completed")
          print(result.output)
          
          # 删除计划
          result = await planner.execute(command="delete", plan_id="plan1")
          print(result.output)

      asyncio.run(main())
      ```

    - **改进建议**：  
      1. **支持并发操作**：目前所有操作都是同步的，如果同时处理多个计划可能出现问题。可考虑引入 `asyncio.Lock`。  
      2. **持久化支持**：当前所有计划数据都存储在内存中，程序重启后会丢失。可以引入数据库或文件系统进行持久化存储。  
      3. **更详细的状态报告**：增加对每个步骤的时间记录（例如开始时间、结束时间）与进度百分比的支持。  
      4. **扩展状态枚举**：允许用户自定义步骤状态或提供更多预定义状态。  
      5. **导出功能**：支持将计划导出为 JSON 或 Markdown 格式，便于共享或备份。  

  - **python_execute.py**  
    - **主要功能**：  
      提供一个可以安全地在隔离环境中执行 Python 代码的工具。支持通过超时机制限制代码执行时间，以防止长时间运行或无限循环的代码影响系统稳定性。  

    - **核心组件与类**：  
      - **`PythonExecute` 类**：  
        - 继承自 `BaseTool`。  
        - 用于执行 Python 代码字符串并捕获标准输出。  
        - 提供了简单的沙盒执行机制，通过限制 `__builtins__` 以减少潜在安全隐患。  
        - 提供超时控制以防止长时间运行的代码。  

    - **支持的输入参数 (`parameters`)**：  
      ```python
      parameters = {
          "type": "object",
          "properties": {
              "code": {
                  "type": "string",
                  "description": "The Python code to execute.",
              },
          },
          "required": ["code"],
      }
      ```
      - `code` (str)：必需，表示要执行的 Python 代码字符串。  

    - **方法与功能**：  
      - `_run_code()`：  
        - 同步执行 Python 代码。  
        - 捕捉 `print()` 函数输出，支持输出重定向。  
        - 将结果保存到共享的 `result_dict` 中，支持并发访问。  
      - `execute()`：  
        - 异步入口方法，用于调用 `_run_code()` 方法。  
        - 提供代码执行的超时机制。  
        - 在超时的情况下，强制终止子进程。  
        - 返回包含 `observation` 和 `success` 的字典。  

    - **设计特点**：  
      - **多进程隔离**：  
        通过使用 Python 的 `multiprocessing` 模块来隔离代码执行，避免代码执行影响到主进程的状态。  
      - **输出捕捉**：  
        通过重定向 `sys.stdout` 将 `print()` 的输出捕捉到字符串中。  
      - **内置安全限制**：  
        代码执行时提供自定义的 `__builtins__` 字典，防止访问系统敏感模块。  
      - **超时机制**：  
        使用 `multiprocessing` 的 `join()` 方法结合 `terminate()` 方法确保在指定时间内终止代码执行。  

    - **代码片段分析**：  
      ```python
      def _run_code(self, code: str, result_dict: dict, safe_globals: dict) -> None:
          original_stdout = sys.stdout
          try:
              output_buffer = StringIO()
              sys.stdout = output_buffer
              exec(code, safe_globals, safe_globals)
              result_dict["observation"] = output_buffer.getvalue()
              result_dict["success"] = True
          except Exception as e:
              result_dict["observation"] = str(e)
              result_dict["success"] = False
          finally:
              sys.stdout = original_stdout
      ```
      - 将 `sys.stdout` 重定向到 `StringIO()` 对象中以捕获输出。  
      - 使用 `exec()` 函数执行代码，并将所有的输出写入到 `result_dict` 中。  
      - 捕捉所有异常并记录为错误消息。  
      - 恢复标准输出为原始的 `sys.stdout`。  

    - **示例调用**：  
      ```python
      import asyncio
      from app.tool.python_execute import PythonExecute

      async def main():
          python_tool = PythonExecute()
          
          # 执行简单的 Python 代码
          result = await python_tool.execute(code="print('Hello World')")
          print(result["observation"])

          # 执行有错误的代码
          result = await python_tool.execute(code="print(1 / 0)")
          print(result["observation"])

          # 执行超时的代码
          result = await python_tool.execute(code="while True: pass", timeout=2)
          print(result["observation"])

      asyncio.run(main())
      ```

    - **输出示例**：  
      ```
      Hello World
      
      division by zero
      
      Execution timeout after 2 seconds
      ```

    - **改进建议**：  
      1. **更强的安全性控制**：当前使用了自定义的 `__builtins__`，但仍然存在潜在的安全风险。可以考虑更严格地限制可用模块和函数。  
      2. **支持返回值捕捉**：目前仅支持 `print()` 的输出捕捉。可以扩展工具支持捕捉函数返回值。  
      3. **日志记录与监控**：增加执行日志记录和性能监控，以更好地分析执行效果与性能问题。  
      4. **沙盒环境优化**：允许自定义全局变量或导入特定模块，以便支持更多的代码执行场景。  
      5. **提高兼容性与安全性**：当前的实现可能在某些系统中受到限制。可以考虑引入更高级别的沙盒技术（如 `Pyodide` 或 `RestrictedPython`）。  



  - **str_replace_editor.py**  
    - **主要功能**：  
      提供对文件和目录进行查看、创建、编辑、插入、字符串替换及撤销编辑的工具。支持本地文件系统与沙盒环境的兼容。  
      允许在文件中执行字符串替换、插入新内容以及回滚最后一次编辑。  

    - **核心组件与类**：  
      - **`StrReplaceEditor` 类**：  
        - 继承自 `BaseTool`。  
        - 提供了以下功能：查看文件/目录内容、创建文件、字符串替换、插入内容、撤销编辑。  
        - 支持对本地文件系统与沙盒环境的操作。  
        - 保存每个文件的编辑历史记录，允许撤销最近一次编辑。  

    - **支持的输入参数 (`parameters`)**：  
      ```python
      parameters = {
          "type": "object",
          "properties": {
              "command": {"type": "string", "enum": ["view", "create", "str_replace", "insert", "undo_edit"]},
              "path": {"type": "string"},
              "file_text": {"type": "string"},
              "old_str": {"type": "string"},
              "new_str": {"type": "string"},
              "insert_line": {"type": "integer"},
              "view_range": {"type": "array", "items": {"type": "integer"}},
          },
          "required": ["command", "path"]
      }
      ```
      - `command`：操作类型，支持 `view`, `create`, `str_replace`, `insert`, `undo_edit`。  
      - `path`：目标文件或目录的路径。  
      - `file_text`：用于 `create` 命令的文件内容。  
      - `old_str`：用于 `str_replace` 命令中要替换的原字符串。  
      - `new_str`：用于 `str_replace` 或 `insert` 命令中的新字符串。  
      - `insert_line`：用于 `insert` 命令中，插入位置的行号。  
      - `view_range`：用于 `view` 命令中指定的文件查看行号范围。  

    - **方法与功能**：  
      - `view()`：查看文件或目录的内容。支持部分文件读取（行号范围）。  
      - `create()`：创建新文件，写入指定内容。  
      - `str_replace()`：对文件中的唯一字符串进行替换操作。  
      - `insert()`：在指定行号之后插入新的字符串。  
      - `undo_edit()`：撤销最近一次编辑。  
      - `_get_operator()`：根据配置选择是使用 `LocalFileOperator` 还是 `SandboxFileOperator`。  
      - `_view_directory()`：查看目录内容，列出最多两层的文件与子目录。  
      - `_view_file()`：查看文件内容，支持行号范围显示与内容截断。  
      - `_make_output()`：格式化输出内容并附加行号信息。  

    - **设计特点**：  
      - **编辑历史管理**：  
        每次文件编辑都会将原内容保存到 `self._file_history` 中，以便进行回滚操作。  
      - **支持目录查看**：  
        如果目标路径是目录，则会列出最多两层的目录与文件。  
      - **字符串替换功能**：  
        仅在唯一匹配的情况下进行替换，避免意外替换多个相同字符串。  
      - **支持插入操作**：  
        可以在指定行号之后插入新的内容。  
      - **查看文件时自动截断长内容**：  
        如果文件内容过长，会自动截断输出，减少输出过载。  
      - **沙盒环境兼容**：  
        支持在沙盒环境下进行文件操作，通过 `config.sandbox.use_sandbox` 控制。  

    - **代码片段分析**：  
      ```python
      async def view(self, path: PathLike, view_range: Optional[List[int]] = None, operator: FileOperator = None) -> CLIResult:
          """Display file or directory content."""
          is_dir = await operator.is_directory(path)

          if is_dir:
              return await self._view_directory(path, operator)
          else:
              return await self._view_file(path, operator, view_range)
      ```
      - 检查目标路径是否为目录，如果是则调用 `_view_directory()`，否则调用 `_view_file()`。  
      - 支持 `view_range` 参数用于部分读取文件内容。  

    - **示例调用**：  
      ```python
      import asyncio
      from app.tool.str_replace_editor import StrReplaceEditor

      async def main():
          editor = StrReplaceEditor()

          # 查看文件内容
          result = await editor.execute(command="view", path="/path/to/file.txt")
          print(result)

          # 创建一个新文件
          result = await editor.execute(command="create", path="/path/to/new_file.txt", file_text="Hello, World!")
          print(result)

          # 替换文件中的特定字符串
          result = await editor.execute(command="str_replace", path="/path/to/file.txt", old_str="Hello", new_str="Hi")
          print(result)

          # 插入新的字符串到指定行后
          result = await editor.execute(command="insert", path="/path/to/file.txt", insert_line=2, new_str="New line inserted")
          print(result)

          # 撤销最后一次编辑
          result = await editor.execute(command="undo_edit", path="/path/to/file.txt")
          print(result)
      
      asyncio.run(main())
      ```

    - **输出示例**：  
      ```
      Here's the result of running `cat -n` on /path/to/file.txt:
           1    This is the original file content.
           2    It has multiple lines.
           3    End of file.

      File created successfully at: /path/to/new_file.txt

      The file /path/to/file.txt has been edited. Here's a snippet of the edited file:
           1    Hi, this is the edited file content.
           2    It has multiple lines.
           3    End of file.

      The file /path/to/file.txt has been edited. Here's a snippet of the edited file:
           1    This is the original file content.
           2    It has multiple lines.
           3    New line inserted
           4    End of file.

      Last edit to /path/to/file.txt undone successfully.
      ```

    - **改进建议**：  
      1. **更强的文件读取与写入安全性**：目前的实现依赖于 `FileOperator`，可以引入更细致的权限管理。  
      2. **多版本编辑历史支持**：允许回滚到更早的版本，而不是仅限于最近一次编辑。  
      3. **自定义输出格式支持**：允许用户指定输出格式（如 Markdown、HTML 等）。  
      4. **异步优化**：可以通过 `aiofiles` 等库来改进文件操作的性能。  


  - **terminate.py**  
    - **主要功能**：  
      提供用于终止与用户交互的工具，当任务完成或助手无法继续时调用。  
      可以明确标记结束状态为 `success` 或 `failure`。  
      常用于执行链的最后一步，确保任务流完整结束。  

    - **核心组件与类**：  
      - **`Terminate` 类**：  
        - 继承自 `BaseTool`。  
        - 提供用于结束任务的 `execute()` 方法。  
        - 定义了两个状态：`success` 和 `failure`。  

    - **支持的输入参数 (`parameters`)**：  
      ```python
      parameters = {
          "type": "object",
          "properties": {
              "status": {
                  "type": "string",
                  "description": "The finish status of the interaction.",
                  "enum": ["success", "failure"],
              }
          },
          "required": ["status"]
      }
      ```
      - `status`：用于指明结束状态。值为 `"success"` 或 `"failure"`。  

    - **方法与功能**：  
      - `execute()`：接收一个字符串参数 `status`，并返回一个表示终止状态的消息。  
        ```python
        async def execute(self, status: str) -> str:
            """Finish the current execution"""
            return f"The interaction has been completed with status: {status}"
        ```
      - 调用后不会进行进一步的处理，是任务流中的最终步骤。  

    - **设计特点**：  
      - **简洁性**：工具结构简单，提供了最小化的功能接口以结束任务流。  
      - **明确的状态标识**：支持 `success` 与 `failure` 两种状态，便于识别交互结果。  
      - **标准化的接口**：继承自 `BaseTool`，与其他工具的调用方式保持一致。  

    - **代码片段分析**：  
      ```python
      terminate_tool = Terminate()
      result = await terminate_tool.execute(status="success")
      print(result)
      ```
      - 在任务完成后调用 `execute()`，传入 `"success"` 或 `"failure"`。  
      - 返回一个字符串格式的确认消息。  

    - **输出示例**：  
      ```python
      The interaction has been completed with status: success
      ```
      或者：  
      ```python
      The interaction has been completed with status: failure
      ```

    - **改进建议**：  
      1. **自定义状态信息支持**：允许用户提供自定义状态或信息（如 `"partial_success"` 或详细的失败原因）。  
      2. **时间戳支持**：在输出中附加任务完成的时间戳。  
      3. **日志记录支持**：在调用后自动记录日志，便于后续追踪或分析。  



  - **tool_collection.py**  
    - **主要功能**：  
      提供一个工具集合管理类 `ToolCollection`，用于对多个工具进行统一的创建、调用、执行、与管理。  
      能够支持工具的动态添加、删除与遍历，并提供批量执行的能力。  
      是整体系统中工具的调度核心模块。  

    - **核心组件与类**：  
      - **`ToolCollection` 类**：  
        - 用于管理多个工具实例的集合。  
        - 支持工具的注册、调用与并行执行。  
        - 提供工具的动态增删功能与执行结果的统一收集。  

    - **工具集合的初始化与配置**：  
      ```python
      class ToolCollection:
          def __init__(self, *tools: BaseTool):
              self.tools = tools
              self.tool_map = {tool.name: tool for tool in tools}
      ```
      - 初始化时支持多个工具同时注册。  
      - `tools` 是一个包含所有工具实例的元组。  
      - `tool_map` 是一个字典，将工具名作为键值用于快速索引。  

    - **支持的主要方法与功能**：  
      1. **工具调用与执行 (`execute`)**：  
          ```python
          async def execute(self, *, name: str, tool_input: Dict[str, Any] = None) -> ToolResult:
              tool = self.tool_map.get(name)
              if not tool:
                  return ToolFailure(error=f"Tool {name} is invalid")
              try:
                  result = await tool(**tool_input)
                  return result
              except ToolError as e:
                  return ToolFailure(error=e.message)
          ```
          - 根据工具名称调用对应工具的 `execute()` 方法。  
          - 支持通过 `tool_input` 提供输入参数。  
          - 捕获执行过程中可能抛出的 `ToolError` 并返回 `ToolFailure`。  

      2. **批量执行所有工具 (`execute_all`)**：  
          ```python
          async def execute_all(self) -> List[ToolResult]:
              results = []
              for tool in self.tools:
                  try:
                      result = await tool()
                      results.append(result)
                  except ToolError as e:
                      results.append(ToolFailure(error=e.message))
              return results
          ```
          - 顺序执行集合中所有工具，并将结果收集为列表返回。  
          - 遇到错误时不会终止整个流程，而是记录失败信息。  

      3. **工具注册与动态添加 (`add_tool`, `add_tools`)**：  
          ```python
          def add_tool(self, tool: BaseTool):
              self.tools += (tool,)
              self.tool_map[tool.name] = tool
              return self

          def add_tools(self, *tools: BaseTool):
              for tool in tools:
                  self.add_tool(tool)
              return self
          ```
          - `add_tool()`：添加单个工具实例，并更新 `tool_map`。  
          - `add_tools()`：支持批量添加工具。  
          - 返回 `self` 以支持链式调用。  

      4. **工具检索 (`get_tool`)**：  
          ```python
          def get_tool(self, name: str) -> BaseTool:
              return self.tool_map.get(name)
          ```
          - 根据工具名称获取对应工具实例。  
          - 若工具不存在则返回 `None`。  

      5. **参数提取 (`to_params`)**：  
          ```python
          def to_params(self) -> List[Dict[str, Any]]:
              return [tool.to_param() for tool in self.tools]
          ```
          - 将所有工具的参数格式化为标准化列表。  
          - 用于生成工具调用的 JSON 格式参数定义。  

    - **设计特点**：  
      - **灵活性高**：支持动态工具注册与调用。  
      - **异步支持**：所有执行方法均为 `async`，支持异步调用与并发执行。  
      - **统一管理**：提供了对所有工具的统一调度接口，简化了工具调用的流程。  
      - **异常捕获与处理**：在工具执行过程中对异常进行捕捉并转化为标准化的 `ToolFailure` 对象。  

    - **使用示例**：  
      ```python
      from app.tool import Bash, WebSearch, ToolCollection

      # 创建工具集合并添加工具
      tools = ToolCollection(Bash(), WebSearch())

      # 异步执行单个工具
      result = await tools.execute(name="bash", tool_input={"command": "ls -l"})
      print(result.output)

      # 异步执行所有工具
      all_results = await tools.execute_all()
      for res in all_results:
          print(res.output)
      ```

    - **改进建议**：  
      1. **支持工具删除 (`remove_tool`)**：添加工具删除功能以提高管理灵活性。  
      2. **支持工具批量调用 (`execute_batch`)**：允许并行调用多个工具，提高效率。  
      3. **支持工具状态监控与日志记录**：引入日志系统与执行状态查询。  
      4. **自动化工具文档生成**：提供工具参数与调用方式的自动化文档生成接口。  


- **web_search.py**  
  - **主要功能**：  
    - 提供多搜索引擎支持的 Web 搜索工具，支持自动切换引擎、异步内容抓取与自定义配置。  
    - 核心功能包括：  
      - **多搜索引擎支持**：Google、Baidu、DuckDuckGo、Bing，可通过配置文件自定义优先级与回退顺序。  
      - **搜索引擎调用与重试机制**：通过 `tenacity` 库实现调用重试，当某个引擎失败时自动尝试其他引擎。  
      - **异步内容抓取**：使用 `asyncio` 与 `requests` 提供的线程池结合，进行非阻塞式内容抓取。  
      - **动态配置支持**：支持通过配置文件自定义搜索参数（语言、国家、重试次数等）。  
      - **结构化输出**：使用 `SearchResponse` 类对搜索结果进行格式化与输出，支持展示内容预览与元数据。  
    
  - **主要类与方法包括**：  
    - `SearchResult`：表示单个搜索结果，包括 URL、标题、描述、源引擎、内容预览等。  
    - `SearchMetadata`：用于存储搜索操作的元数据，如总结果数、语言代码与国家代码。  
    - `SearchResponse`：继承自 `ToolResult`，用于封装搜索结果与元数据，并提供格式化输出方法。  
    - `WebContentFetcher`：提供 `fetch_content()` 方法，支持异步抓取网页内容并进行 HTML 内容解析与提取。  
    - `WebSearch`：核心搜索工具类，包含以下功能：  
      - `_try_all_engines()`：按照配置文件指定的顺序，尝试所有搜索引擎并处理结果。  
      - `_fetch_content_for_results()`：为搜索结果异步抓取网页内容。  
      - `_get_engine_order()`：根据配置文件决定搜索引擎调用的优先级与顺序。  
      - `_perform_search_with_engine()`：执行具体搜索引擎的查询，并返回 `SearchItem` 列表。  
      - `execute()`：入口方法，执行搜索查询并根据配置返回结构化的结果。  
    
  - **依赖库与工具**：  
    - `requests`、`asyncio`、`BeautifulSoup`：用于异步请求与 HTML 内容解析。  
    - `pydantic`：用于定义数据模型与自动验证。  
    - `tenacity`：实现重试机制与指数回退。  
    - `config`：用于加载配置参数，包括搜索引擎优先级、重试次数、语言与国家设置。  
    - `logger`：用于记录搜索操作与异常情况。  
    
  - **适用场景**：  
    - 聚合多个搜索引擎的查询结果，提高搜索精度与覆盖率。  
    - 提供异步内容抓取能力，可用于自动化信息采集与数据分析。  
    - 与 `WenCFO Agent` 或 `OpenManus` 集成，用于实时信息检索与网页内容分析。  


- **search/** 子目录：  
  - **\_\_init\_\_.py**：  
    - **功能描述：**  
      - 作为 `search` 模块的初始化文件，定义并暴露统一的搜索引擎接口集合。  
      - 将不同搜索引擎的实现类统一导入，并通过 `__all__` 列表声明对外可访问的模块和类。  
      - 确保搜索引擎模块的外部调用时，只需引入这一接口模块即可访问所有支持的搜索引擎。  
      - 提高模块的组织性与易用性，避免外部系统直接依赖于每一个具体实现文件。  
      - 支持的搜索引擎包括：`WebSearchEngine`、`BaiduSearchEngine`、`DuckDuckGoSearchEngine`、`GoogleSearchEngine`、`BingSearchEngine`。  


  - **baidu_search.py**：  
    - **功能描述：**  
      - 提供 `BaiduSearchEngine` 类的实现，负责与百度搜索引擎交互并解析返回结果。  
      - 使用 `baidusearch` 库进行百度搜索，并支持自定义返回结果数量。  
      - 从搜索结果中提取标题 (`title`)、URL (`url`)、描述 (`description`) 并封装为 `SearchItem` 对象。  
      - 提供标准化接口 `perform_search()`，支持外部系统按统一格式调用。  
      - 处理百度搜索返回的不同格式数据（字符串形式、字典形式、对象形式），确保兼容性与稳定性。  
      - 能够处理百度的简单搜索请求，不支持高级搜索（如图片、视频等搜索）。  

  - **base.py**：  
    - **功能描述：**  
      - 定义搜索引擎模块的基础类 `WebSearchEngine` 和数据模型 `SearchItem`。  
      - **SearchItem：** 封装了搜索结果的数据结构，提供标准字段：  
        - `title`：搜索结果的标题。  
        - `url`：搜索结果的链接地址。  
        - `description`：搜索结果的简要描述或摘要（可选）。  
      - 提供统一的输出格式，确保不同搜索引擎的结果能够以相同的数据结构呈现。  
      - **WebSearchEngine：** 抽象基类，定义了所有搜索引擎实现必须遵循的接口：  
        - `perform_search()`：接受查询字符串与参数，返回 `SearchItem` 列表。  
      - 强制所有搜索引擎实现必须定义 `perform_search()` 方法，以确保接口一致性。  
      - 提供模块化架构，使不同的搜索引擎实现能够轻松集成与替换。  

  - **bing_search.py**：  
    - **功能描述：**  
      - 提供 `BingSearchEngine` 类的实现，通过模拟 HTTP 请求与 `BeautifulSoup` 解析 `Bing` 搜索页面。  
      - 支持从 `Bing` 搜索页面中提取标题、URL、描述，并支持翻页请求。  
      - 实现 `perform_search()` 接口，确保与其他引擎实现的调用格式一致。  
      - 使用自定义请求头与 `User-Agent` 模拟不同浏览器访问 `Bing` 搜索。  
      - 支持解析多个页面，按需求返回指定数量的搜索结果。  
      - 提供 HTML 内容解析逻辑，包括：  
        - 查找结果列表 (`<ol>` 元素) 并提取 `<li>` 元素中的标题、链接与摘要。  
        - 自动识别下一页按钮并继续请求，支持分页抓取。  
      - 可用于通用信息搜索与数据抓取，不支持高级搜索选项（如图片、新闻等）。  

  - **duckduckgo_search.py**：  
    - **功能描述：**  
      - 提供 `DuckDuckGoSearchEngine` 类的实现，通过 `duckduckgo_search` 库进行搜索并解析结果。  
      - 支持从 DuckDuckGo 搜索中提取标题、URL 和描述，并格式化为标准化的 `SearchItem` 对象。  
      - 实现 `perform_search()` 接口，确保与其他搜索引擎实现的调用格式一致。  
      - 提供简单、隐私友好的搜索服务，无需 API 密钥或复杂配置。  
      - 支持从返回的数据结构中提取所需信息，自动转换为 `SearchItem` 格式。  
      - 不依赖于 HTML 解析器，直接使用库提供的接口进行数据提取。  
      - 可用于通用信息搜索与数据采集，支持中文与英文搜索。  


  - **google_search.py**：  
    - **功能描述：**  
      - 提供 `GoogleSearchEngine` 类的实现，基于 `googlesearch` 库进行 Google 搜索并解析结果。  
      - 支持从 Google 搜索结果中提取标题、URL 和描述，并格式化为标准化的 `SearchItem` 对象。  
      - 实现 `perform_search()` 接口，确保与其他搜索引擎实现的调用格式一致。  
      - 支持自定义返回结果数量，允许设置 `num_results` 参数以控制输出条数。  
      - 使用标准化的数据结构 (`SearchItem`) 确保与其他搜索引擎实现的兼容性。  
      - 提供简单接口调用，无需复杂配置或 API 密钥。  
      - 可用于通用信息搜索，但不支持高级功能（如图片、视频搜索等）。  



#### G. app 根目录其他文件
- **\_\_init\_\_.py**  
  - **主要功能**：  
    - 检查 Python 版本的兼容性，确保运行环境在 Python 3.11 至 3.13 之间。  
    - 如果检测到不兼容的 Python 版本，会输出警告信息：  
      ```
      Warning: Unsupported Python version {ver}, please use 3.11-3.13
      ```
    - 不包含任何模块的初始化逻辑，仅用于环境检查。  

- **bedrock.py**  
  - **主要功能**：  
    - 提供与 AWS Bedrock 服务交互的客户端接口，支持对 `chat completion` 功能的调用。  
    - 封装了消息格式转换、工具调用映射、流式与非流式请求等功能。  
    - 主要类与方法包括：  
      - `BedrockClient`：初始化与 AWS Bedrock 的连接，并提供 `chat` 接口。  
      - `Chat`：提供 `completions` 接口，用于调用 `ChatCompletions` 类。  
      - `ChatCompletions`：核心处理类，包含以下功能：  
        - `_convert_openai_tools_to_bedrock_format()`：将 OpenAI 风格的工具调用格式转换为 Bedrock 格式。  
        - `_convert_openai_messages_to_bedrock_format()`：将 OpenAI 消息格式转为 Bedrock 所需的格式。  
        - `_convert_bedrock_response_to_openai_format()`：将 Bedrock 响应格式转为 OpenAI 风格的输出。  
        - `_invoke_bedrock()`：非流式的模型调用接口。  
        - `_invoke_bedrock_stream()`：支持流式输出的模型调用接口。  
        - `create()`：主入口方法，根据 `stream` 参数决定使用流式或非流式调用方式。  
    - 依赖于 `boto3` 库来与 AWS Bedrock 服务交互。  
    - 引入了全局变量 `CURRENT_TOOLUSE_ID` 用于跨请求跟踪工具调用的状态。  

- **config.py**  
  - **主要功能**：  
    - 配置管理模块，负责加载、解析、验证并提供统一的应用配置接口。  
    - 支持以下配置类型：  
      - **LLMSettings**：语言模型设置（如模型名称、API 版本、最大 token 数、温度参数等）。  
      - **ProxySettings**：代理设置（如服务器地址、用户名、密码）。  
      - **SearchSettings**：搜索引擎配置，包括主要引擎与备用引擎、重试次数与延迟、语言与国家代码。  
      - **BrowserSettings**：浏览器配置，包括无头模式、安全配置、代理设置等。  
      - **SandboxSettings**：沙箱配置（使用 Docker 等容器技术），支持限制内存、CPU、网络等。  
      - **MCPSettings**：MCP（Model Context Protocol）的配置。  
    - 通过 `tomllib` 解析配置文件 (`config.toml`) 并加载至 `AppConfig` 对象中。  
    - 配置文件的加载顺序：  
      - 查找 `config/config.toml` 文件；  
      - 若找不到，则尝试加载 `config/config.example.toml`。  
    - 提供了一个全局 `config` 实例，通过 `Config` 单例类实现线程安全。  
    - 配置值可以通过属性访问，如 `config.llm`, `config.browser_config`, `config.sandbox` 等。  

- **exceptions.py**  
  - **主要功能**：  
    - 定义 OpenManus 模块中的自定义异常类型，以便于在不同组件中统一处理错误。  
    - 主要异常类：  
      - `ToolError`：当工具调用过程中出现错误时抛出。  
        - 属性：`message` - 错误信息描述。  
      - `OpenManusError`：OpenManus 模块的基础异常类，所有自定义异常应继承自此类。  
      - `TokenLimitExceeded`：当超过设定的 token 数量限制时抛出。  
  - 用途：为模块内部的错误处理提供统一的异常层次结构。  

- **llm.py**  
  - **主要功能**：  
    - 提供与各种语言模型（LLM）的接口，包括 OpenAI、Azure、AWS Bedrock 等。  
    - 支持多种输入形式（文本、图片、工具调用）并进行统一格式化和验证。  
    - 通过异步接口与模型进行交互，并支持流式输出与非流式输出。  
    - 引入了自定义的 `TokenCounter` 类用于计算消息、工具调用、图片等的 token 数量。  

  - **主要组件与类**：  
    - `LLM`：核心类，负责模型的初始化与调用。  
      - 自动检测模型类型（如 OpenAI, Azure, AWS Bedrock）。  
      - 支持不同的输入形式（文本、图片、工具调用）。  
      - 提供了流式与非流式的请求方式。  
      - 支持 token 计数与限制检查，并记录累计使用情况。  
      - 提供 `ask()`、`ask_with_images()` 和 `ask_tool()` 方法用于不同的任务类型。  
    - `TokenCounter`：用于计算 token 数量的工具类。  
      - 支持对文本、图片和工具调用进行 token 计算。  
      - 提供自定义的高精度图片 token 计算方法。  

  - **主要方法**：  
    - `ask()`：发送文本输入并获取响应，支持流式与非流式请求。  
    - `ask_with_images()`：发送包含图片的输入并获取响应，仅支持支持多模态输入的模型。  
    - `ask_tool()`：通过工具或函数调用与模型交互并获取响应。  
    - `count_message_tokens()`：计算输入消息的总 token 数量。  
    - `check_token_limit()`：检查输入是否超过 token 限制。  
    - `update_token_count()`：更新累计的 token 使用情况。  

  - **支持的模型类型**：  
    - OpenAI（`AsyncOpenAI`）  
    - Azure OpenAI（`AsyncAzureOpenAI`）  
    - AWS Bedrock（`BedrockClient`）  

  - **异常处理**：  
    - 自定义的 `TokenLimitExceeded` 异常用于在超过 token 限制时抛出。  
    - 使用 `tenacity` 库提供的重试机制自动处理 API 调用失败。  

  - **日志记录**：  
    - 引入了 `logger` 模块用于记录请求与错误信息。  

- **logger.py**  
  - **主要功能**：  
    - 提供全局的日志记录功能，基于 `loguru` 库实现。  
    - 支持控制台输出与文件输出两种日志记录方式，并支持动态调整日志级别。  
    - 日志文件按当前时间戳命名并保存在 `logs/` 目录下。  

  - **主要组件与函数**：  
    - `define_log_level()`：定义日志输出配置。  
      - 参数：  
        - `print_level`：控制台输出的日志级别（默认：`INFO`）。  
        - `logfile_level`：日志文件记录的日志级别（默认：`DEBUG`）。  
        - `name`：用于为日志文件添加前缀名称。  
      - 返回：配置好的 `loguru` 日志实例。  
    - `logger`：全局的日志实例，由 `define_log_level()` 函数创建。  

  - **日志格式与存储路径**：  
    - 控制台日志：通过 `sys.stderr` 输出，默认级别为 `INFO`。  
    - 文件日志：保存在项目根目录下的 `logs/` 文件夹内，文件名格式为 `name_YYYYMMDDHHMMSS.log` 或 `YYYYMMDDHHMMSS.log`。  
    - 日志记录目录的路径由 `PROJECT_ROOT` 变量指定。  

  - **示例使用**：  
    ```python
    from app.logger import logger

    logger.info("This is an info message")
    logger.debug("This is a debug message")
    logger.error("This is an error message")
    ```

  - **注意事项**：  
    - 在项目启动时调用 `define_log_level()` 以确保日志配置正确加载。  
    - 日志目录 `logs/` 必须存在，否则会引发错误。  

- **schema.py**  
  - **主要功能**：  
    - 定义 OpenManus 模块中使用的核心数据结构与类型，确保在模块间进行数据传递时的格式一致性与类型安全。  
    - 提供标准化的消息格式、工具调用定义、消息角色、工具选择类型、内存管理等功能。  

  - **主要组件与类**：  
    - `Role`：定义消息的角色类型，包括 `SYSTEM`, `USER`, `ASSISTANT`, `TOOL`。  
      - `ROLE_VALUES`：所有有效的角色类型值。  
      - `ROLE_TYPE`：角色类型的类型注解。  
    - `ToolChoice`：定义工具选择策略，包括 `NONE`, `AUTO`, `REQUIRED`。  
      - `TOOL_CHOICE_VALUES`：所有有效的工具选择策略。  
      - `TOOL_CHOICE_TYPE`：工具选择策略的类型注解。  
    - `AgentState`：定义代理的执行状态，包括 `IDLE`, `RUNNING`, `FINISHED`, `ERROR`。  
    - `Function`：定义工具调用的基本结构，包括 `name` 和 `arguments`。  
    - `ToolCall`：定义工具调用的格式，包含 `id`, `type`, `function` 等字段。  
    - `Message`：定义会话中的消息结构。  
      - 支持对话角色、内容、工具调用、图片等字段。  
      - 提供多种创建消息的类方法：`user_message()`, `system_message()`, `assistant_message()`, `tool_message()`。  
      - 提供从工具调用列表创建消息的类方法：`from_tool_calls()`。  
      - 支持与列表或其他消息对象的加法操作。  
      - 支持将消息转换为字典格式 (`to_dict()`)。  
    - `Memory`：用于管理消息的存储与检索。  
      - 支持添加单条或多条消息 (`add_message()`, `add_messages()`)。  
      - 支持按数量检索最近的消息 (`get_recent_messages()`)。  
      - 支持将内存中的消息转为字典列表格式 (`to_dict_list()`)。  

  - **用途与作用**：  
    - 确保不同模块之间的数据传递结构化、规范化。  
    - 提供一套标准的消息格式接口，便于与 LLM 进行对话或调用工具。  
    - 提供消息存储与回溯的功能，便于实现长对话记忆或历史记录查询。  


---

### 2. open_manus 模块其他目录与文件

#### A. config 目录
- **config.toml**  
  - 系统主要配置文件，定义了代理参数、工具选项、流程设定等关键参数。 **[猜测]**

#### B. examples 目录
- **benchmarks/**  
  - 包含用于性能测试或任务比较的基准示例。 **[猜测]**
- **use_case/**  
  - 展示实际使用场景和案例，帮助理解如何应用各模块功能。 **[猜测]**

#### C. logs 目录
- 存放运行过程中生成的日志文件，用于调试和监控。 **[猜测]**

#### D. tests 目录
- **sandbox/**  
  - 包含针对沙箱模块的单元测试文件：
    - **test_client.py**：针对 LocalSandboxClient 提供全面单元测试，包括使用 SandboxSettings 配置参数（image、work_dir、memory_limit、cpu_limit）测试沙箱环境的创建；
    - **test_docker_terminal.py**：测试与 Docker 终端的交互功能。 **[猜测]**
    - **test_sandbox_manager.py**：测试沙箱管理器的行为。 **[猜测]**
    - **test_sandbox.py**：测试沙箱核心功能。 **[猜测]**

#### E. workspace 目录
- **workspace/example.txt**  
  - **主要功能**：  
    - 存储示例内容，用于演示 OpenManus 默认的工作文件存储目录。  
  - **内容说明**：  
    - 文件内容为：  
      > This is a sample file. Files generated by OpenManus are stored in the current folder by default.

#### F. open_manus 模块根目录文件

- **main.py**  
  - **主要功能**：   
    - 该文件作为 OpenManus 模块的主要入口，使用异步方式运行。  
    - 导入了 `app.agent.manus` 中的 `Manus` 类和日志记录器 `logger`。  
    - 在 `main()` 异步函数中：  
      - 创建 `Manus` 代理实例；  
      - 从标准输入读取用户提示，若提示为空则记录警告；  
      - 启动代理的 `run` 方法处理提示，并记录处理状态；  
      - 捕获 `KeyboardInterrupt` 异常并记录中断信息；  
      - 在 `finally` 块中调用 `agent.cleanup()` 确保资源清理。  
    - 通过 `asyncio.run(main())` 启动整个流程.

- **run_flow.py**  
  - **主要功能**：  
    - 该文件作为任务流程执行入口，使用异步方式运行任务规划流程。  
    - 导入了 `app.agent.manus` 中的 `Manus` 类、`FlowFactory` 和 `FlowType` 用于创建任务流程，以及日志记录器 `logger`。  
    - 在 `run_flow()` 异步函数中：  
      - 初始化一个包含 `Manus` 实例的代理字典。  
      - 从标准输入读取用户提示，若提示为空或仅为空格则记录警告并终止执行。  
      - 通过 `FlowFactory.create_flow()` 创建一个规划流程实例，指定流程类型为 `FlowType.PLANNING` 并传入代理字典。  
      - 记录“Processing your request...”提示，并调用流程的 `execute(prompt)` 方法异步执行任务，同时使用 `asyncio.wait_for()` 设置 1 小时的超时时间。  
      - 计算并记录任务执行的耗时，输出处理结果。  
      - 捕获 `asyncio.TimeoutError`：当任务超时后记录错误信息，并提示用户尝试简化请求。  
    - 捕获 `KeyboardInterrupt` 异常和其它异常，分别记录取消操作和错误信息。  
    - 通过 `asyncio.run(run_flow())` 启动整个异步流程.

- **run_mcp_server.py**  
  - **主要功能**：  
    - 该文件用于启动 OpenManus MCP 服务器，同时解决部分导入问题。  
    - 导入了 `app.mcp.server` 中的 `MCPServer` 类和 `parse_args` 函数。  
    - 在主程序中：  
      - 调用 `parse_args()` 解析命令行参数；  
      - 创建 `MCPServer` 实例；  
      - 调用 `server.run()` 启动服务器，并将解析的 `transport` 参数传入以决定通信方式.

- **run_mcp.py**  
  - **主要功能**：  
    - 该文件作为 MCP Agent 的入口，用于启动 MCP 代理并处理命令行参数。  
    - 通过命令行参数决定 MCP 代理的连接方式（`stdio` 或 `sse`）、是否以交互模式运行，或仅执行单个提示。  
  - **主要实现细节**：  
    - **导入模块**：  
      - 使用 `argparse` 解析命令行参数。  
      - 使用 `asyncio` 处理异步任务，`sys` 处理系统调用。  
      - 从 `app.agent.mcp` 导入 `MCPAgent`；从 `app.config` 获取配置信息（如 `root_path` 和 `mcp_config.server_reference`）；从 `app.logger` 导入日志记录器 `logger`。  
    - **MCPRunner 类**：  
      - **作用**：封装 MCPAgent 的初始化、运行和资源清理逻辑。  
      - **初始化**：  
        - 从配置中获取 `root_path` 和 `server_reference`。  
        - 创建 `MCPAgent` 实例。  
      - **方法**：  
        - `initialize(connection_type, server_url=None)`：  
          - 根据 `connection_type`（`stdio` 或 `sse`）初始化 MCPAgent。  
          - 当使用 `stdio` 连接时，调用 `agent.initialize`，传入当前 Python 解释器及模块启动参数；  
          - 当使用 `sse` 连接时，传入 `server_url`。  
          - 记录初始化和连接状态。  
        - `run_interactive()`：  
          - 进入交互模式，提示用户输入请求，直到输入 "exit"、"quit" 或 "q" 退出。  
          - 对每个输入调用 `agent.run()` 并输出返回结果。  
        - `run_single_prompt(prompt)`：  
          - 使用单个提示调用 `agent.run()`。  
        - `run_default()`：  
          - 默认模式下，从标准输入读取提示，若输入有效则调用 `agent.run()` 处理请求。  
        - `cleanup()`：  
          - 调用 `agent.cleanup()` 清理资源，并记录会话结束。  
    - **命令行参数解析**：  
      - 使用 `parse_args()` 函数解析参数：  
        - `--connection` (`-c`)：选择连接方式，默认为 `stdio`。  
        - `--server-url`：指定 SSE 连接的 URL。  
        - `--interactive` (`-i`)：是否以交互模式运行。  
        - `--prompt` (`-p`)：传入单个提示后立即执行并退出。  
    - **主流程 `run_mcp()`**：  
      - 解析命令行参数，创建 `MCPRunner` 实例并初始化代理连接；  
      - 根据命令行参数决定执行单个提示、交互模式或默认模式；  
      - 捕获 `KeyboardInterrupt` 和其他异常，并在出现异常时记录错误信息；  
      - 在最后调用 `cleanup()` 确保资源被释放。  
    - **启动入口**：  
      - 在 `if __name__ == "__main__":` 块中，通过 `asyncio.run(run_mcp())` 启动整个异步流程。

- **setup.py**  
  - **主要功能**：  
    - 该文件用于打包、分发和安装 OpenManus 模块，基于 setuptools 实现。  
    - 读取 `README.md` 作为长描述，设置项目元数据（如项目名称、版本、作者、描述、依赖项等），并配置控制台脚本入口。  
  - **主要实现细节**：  
    - **读取长描述**：  
      - 使用 `with open("README.md", "r", encoding="utf-8") as fh` 读取 README 文件内容，并赋值给 `long_description`。  
    - **调用 setup()**：  
      - 通过 `setup()` 函数传入项目元数据，包括：  
        - **name**：项目名称为 "openmanus"。  
        - **version**：版本号 "0.1.0"。  
        - **author/author_email**：作者信息及联系方式。  
        - **description**：简短描述项目功能。  
        - **long_description** 与 **long_description_content_type**：使用 README.md 的内容作为长描述，并指定 Markdown 格式。  
        - **url**：项目主页链接。  
        - **packages**：调用 `find_packages()` 自动查找项目内所有包。  
        - **install_requires**：列出项目运行所需的依赖包及其版本要求。  
        - **classifiers**：指定项目的分类器信息，如 Python 版本、许可协议及操作系统要求。  
        - **python_requires**：规定 Python 版本要求为 ">=3.12"。  
        - **entry_points**：配置控制台脚本入口，将命令 `openmanus` 映射到模块 `main` 的 `main` 函数。  


---

## 七、总结

- 本文档旨在为整合 WenCFO Agent 与 OpenManus 模块提供一个全面、抽象的说明，便于在后续逐步查看具体文件内容时更新【猜测】部分，并明确各模块功能与调用关系。
- 下次继续交流时，请根据实际提供的具体脚本内容，我们将进一步细化和确认各部分的描述，同时讨论如何将各功能整合进现有系统。

初始OpenManus核心文件
```
WenCFO Agent
- backend
  - main.py，后端应用，Fast API Web，用来创建一个聊天接口
- docs
  - backup，备份文件  
  - V1，存放V1版本的相关文件 
- www 
  - index.html，一个简易的前端页面，用于和后端Fast API聊天接口交互
- open_manus
  - app
    - agent
      - __init__.py
      - base.py
      - browser.py
      - manus.py
      - mcp.py
      - react.py
      - swe.py
      - toolcall.py
    - flow
      - __init__.py
      - base.py
      - flow_factory.py
      - planning.py
    - mcp
      - __init__.py
      - server.py
    - prompt
      - __init__.py
      - browser.py
      - cot.py
      - manus.py
      - mcp.py
      - planning.py
      - swe.py
      - toolcall.py
    - sandbox
      - __init__.py
      - client.py
      - core
        - exceptions.py 
        - manager.py
        - sandbox.py
        - terminal.py
    - tool
      - __init__.py
      - base.py
      - bash.py
      - browser_use_tool.py
      - create_chat_completion.py
      - deep_research.py
      - file_operators.py
      - mcp.py
      - planning.py
      - python_execute.py
      - str_replace_editor.py
      - terminate.py
      - tool_collection.py
      - web_search.py
      - search
        - __init__.py
        - baidu_search.py
        - base.py
        - bing_search.py
        - duckduckgo_search.py
        - google_search.py 
    - __init__.py
    - bedrock.py
    - config.py
    - exceptions.py
    - llm.py
    - logger.py
    - schema.py
  - config
    - config.toml
  - examples
    - benchmarks
    - use_case
  - logs
  - tests
    - sandbox
      - test_client.py 
      - test_docker_terminal.py
      - test_sandbox_manager.py
      - test_sandbox.py
  - workspace
    - example.txt
  - main.py
  - run_flow.py
  - run_mcp_server.py
  - run_mcp.py
  - setup.py
```