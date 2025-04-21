Un-solved bugs:
1. The manus tool chains cannot stop when the task is finished. Might need check the terminate tool's content and optimize the tool chain processings.
2. 消息流最终返回的时候仍然加上了tool指示，这里其实是不需要加的
3. 参见V0.13/回复中的多重工具使用错误，当用户问你会什么的时候，会错误把工具命令进行多次展示。这是一个潜在可能的大问题，可能会导致系统后续被注入攻击（Prompt Injection），所以需要重新考虑一下工具命令的调用方式。这个更像是一种 Prompt Drift: 指令偏移，即用户的prompt造成了LLM对工具调用指令的误判。

需要update的内容：
1. 前端页面可以刷新显示工作区新获得的文件，但是不能通过浏览器下载。如果想通过浏览器下载，可能要推荐使用FastAPI后端框架设置一个下载端口，来实现下载功能。