"""
基本面分析师 - 统一工具架构版本
使用统一工具自动识别股票类型并调用相应数据源
"""

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage


def create_fundamentals_analyst(llm, toolkit):
    def fundamentals_analyst_node(state):
        print(f"📊 [DEBUG] ===== 基本面分析师节点开始 =====")

        current_date = state["trade_date"]
        ticker = state["company_of_interest"]

        # 🔧 基本面分析数据范围：固定获取10天数据（处理周末/节假日/数据延迟）
        from datetime import datetime, timedelta
        try:
            end_date_dt = datetime.strptime(current_date, "%Y-%m-%d")
            start_date_dt = end_date_dt - timedelta(days=10)
            start_date = start_date_dt.strftime("%Y-%m-%d")
            print(f"📅 [基本面分析师] 数据范围: {start_date} 至 {current_date} (固定10天)")
        except Exception as e:
            print(f"⚠️ [基本面分析师] 日期解析失败，使用默认范围: {e}")
            start_date = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

        print(f"📊 [DEBUG] 输入参数: ticker={ticker}, date={current_date}")
        print(f"📊 [DEBUG] 当前状态中的消息数量: {len(state.get('messages', []))}")
        print(f"📊 [DEBUG] 现有基本面报告: {state.get('fundamentals_report', 'None')[:100]}...")

        # 获取股票市场信息
        from tradingagents.utils.stock_utils import StockUtils
        print(f"📊 [基本面分析师] 正在分析股票: {ticker}")

        market_info = StockUtils.get_market_info(ticker)
        print(f"📊 [DEBUG] 股票类型检查: {ticker} -> {market_info['market_name']} ({market_info['currency_name']})")
        print(f"📊 [DEBUG] 详细市场信息: is_china={market_info['is_china']}, is_hk={market_info['is_hk']}, is_us={market_info['is_us']}")
        print(f"📊 [DEBUG] 工具配置检查: online_tools={toolkit.config['online_tools']}")

        # 选择工具
        if toolkit.config["online_tools"]:
            # 使用统一的基本面分析工具，工具内部会自动识别股票类型
            print(f"📊 [基本面分析师] 使用统一基本面分析工具，自动识别股票类型")
            tools = [toolkit.get_stock_fundamentals_unified]
            print(f"📊 [DEBUG] 选择的工具: {[tool.name for tool in tools]}")
            print(f"📊 [DEBUG] 🔧 统一工具将自动处理: {market_info['market_name']}")
        else:
            tools = [
                toolkit.get_finnhub_company_insider_sentiment,
                toolkit.get_finnhub_company_insider_transactions,
                toolkit.get_simfin_balance_sheet,
                toolkit.get_simfin_cashflow,
                toolkit.get_simfin_income_stmt,
            ]

        # 统一的系统提示，适用于所有股票类型
        system_message = (
            f"你是一位专业的股票基本面分析师。"
            f"⚠️ 绝对强制要求：你必须调用工具获取真实数据！不允许任何假设或编造！"
            f"任务：分析股票代码 {ticker} ({market_info['market_name']})"
            f"🔴 立即调用 get_stock_fundamentals_unified 工具"
            f"参数：ticker='{ticker}', start_date='{start_date}', end_date='{current_date}', curr_date='{current_date}'"
            "📊 分析要求："
            "- 基于真实数据进行深度基本面分析"
            f"- 计算并提供合理价位区间（使用{market_info['currency_name']}{market_info['currency_symbol']}）"
            "- 分析当前股价是否被低估或高估"
            "- 提供基于基本面的目标价位建议"
            "- 包含PE、PB、PEG等估值指标分析"
            "- 结合市场特点进行分析"
            "🌍 语言和货币要求："
            "- 所有分析内容必须使用中文"
            "- 投资建议必须使用中文：买入、持有、卖出"
            "- 绝对不允许使用英文：buy、hold、sell"
            f"- 货币单位使用：{market_info['currency_name']}（{market_info['currency_symbol']}）"
            "🚫 严格禁止："
            "- 不允许说'我将调用工具'"
            "- 不允许假设任何数据"
            "- 不允许编造公司信息"
            "- 不允许直接回答而不调用工具"
            "- 不允许回复'无法确定价位'或'需要更多信息'"
            "- 不允许使用英文投资建议（buy/hold/sell）"
            "✅ 你必须："
            "- 立即调用统一基本面分析工具"
            "- 等待工具返回真实数据"
            "- 基于真实数据进行分析"
            "- 提供具体的价位区间和目标价"
            "- 使用中文投资建议（买入/持有/卖出）"
            "现在立即开始调用工具！不要说任何其他话！"
        )

        # 系统提示模板
        system_prompt = (
            "🔴 强制要求：你必须调用工具获取真实数据！"
            "🚫 绝对禁止：不允许假设、编造或直接回答任何问题！"
            "✅ 你必须：立即调用提供的工具获取真实数据，然后基于真实数据进行分析。"
            "可用工具：{tool_names}。\n{system_message}"
            "当前日期：{current_date}。分析目标：{ticker}。"
        )

        # 创建提示模板
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ])

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        # 检测阿里百炼模型并创建新实例
        if hasattr(llm, '__class__') and 'DashScope' in llm.__class__.__name__:
            print(f"📊 [DEBUG] 检测到阿里百炼模型，创建新实例以避免工具缓存")
            from tradingagents.llm_adapters import ChatDashScopeOpenAI

            # 获取原始 LLM 的 base_url 和 api_key
            original_base_url = getattr(llm, 'openai_api_base', None)
            original_api_key = getattr(llm, 'openai_api_key', None)

            llm = ChatDashScopeOpenAI(
                model=llm.model_name,
                api_key=original_api_key,  # 🔥 传递原始 LLM 的 API Key
                base_url=original_base_url if original_base_url else None,  # 传递 base_url
                temperature=llm.temperature,
                max_tokens=getattr(llm, 'max_tokens', 2000)
            )

            if original_base_url:
                print(f"📊 [DEBUG] 新实例使用原始 base_url: {original_base_url}")
            if original_api_key:
                print(f"📊 [DEBUG] 新实例使用原始 API Key（来自数据库配置）")

        print(f"📊 [DEBUG] 创建LLM链，工具数量: {len(tools)}")
        print(f"📊 [DEBUG] 绑定的工具列表: {[tool.name for tool in tools]}")
        print(f"📊 [DEBUG] 创建工具链，让模型自主决定是否调用工具")

        try:
            chain = prompt | llm.bind_tools(tools)
            print(f"📊 [DEBUG] ✅ 工具绑定成功，绑定了 {len(tools)} 个工具")
        except Exception as e:
            print(f"📊 [DEBUG] ❌ 工具绑定失败: {e}")
            raise e

        print(f"📊 [DEBUG] 调用LLM链...")
        result = chain.invoke(state["messages"])
        print(f"📊 [DEBUG] LLM调用完成")

        print(f"📊 [DEBUG] 结果类型: {type(result)}")
        print(f"📊 [DEBUG] 工具调用数量: {len(result.tool_calls) if hasattr(result, 'tool_calls') else 0}")
        print(f"📊 [DEBUG] 内容长度: {len(result.content) if hasattr(result, 'content') else 0}")

        # 检查工具调用
        expected_tools = [tool.name for tool in tools]
        actual_tools = [tc['name'] for tc in result.tool_calls] if hasattr(result, 'tool_calls') and result.tool_calls else []
        
        print(f"📊 [DEBUG] 期望的工具: {expected_tools}")
        print(f"📊 [DEBUG] 实际调用的工具: {actual_tools}")

        # 处理基本面分析报告
        if hasattr(result, 'tool_calls') and len(result.tool_calls) > 0:
            # 有工具调用，记录工具调用信息
            tool_calls_info = []
            for tc in result.tool_calls:
                tool_calls_info.append(tc['name'])
                print(f"📊 [DEBUG] 工具调用 {len(tool_calls_info)}: {tc}")
            
            print(f"📊 [基本面分析师] 工具调用: {tool_calls_info}")
            
            # 返回状态，让工具执行
            return {"messages": [result]}
        
        else:
            # 没有工具调用，使用阿里百炼强制工具调用修复
            print(f"📊 [DEBUG] 检测到模型未调用工具，启用强制工具调用模式")
            
            # 强制调用统一基本面分析工具
            try:
                print(f"📊 [DEBUG] 强制调用 get_stock_fundamentals_unified...")
                unified_tool = next((tool for tool in tools if tool.name == 'get_stock_fundamentals_unified'), None)
                if unified_tool:
                    combined_data = unified_tool.invoke({
                        'ticker': ticker,
                        'start_date': start_date,
                        'end_date': current_date,
                        'curr_date': current_date
                    })
                    print(f"📊 [DEBUG] 统一工具数据获取成功，长度: {len(combined_data)}字符")
                else:
                    combined_data = "统一基本面分析工具不可用"
                    print(f"📊 [DEBUG] 统一工具未找到")
            except Exception as e:
                combined_data = f"统一基本面分析工具调用失败: {e}"
                print(f"📊 [DEBUG] 统一工具调用异常: {e}")
            
            currency_info = f"{market_info['currency_name']}（{market_info['currency_symbol']}）"
            
            # 生成基于真实数据的分析报告
            analysis_prompt = f"""基于以下真实数据，对股票{ticker}进行详细的基本面分析：

{combined_data}

请提供：
1. 公司基本信息分析
2. 财务状况评估
3. 盈利能力分析
4. 估值分析（使用{currency_info}）
5. 投资建议（买入/持有/卖出）

要求：
- 基于提供的真实数据进行分析
- 价格使用{currency_info}
- 投资建议使用中文
- 分析要详细且专业"""

            try:
                # 创建简单的分析链
                analysis_prompt_template = ChatPromptTemplate.from_messages([
                    ("system", "你是专业的股票基本面分析师，基于提供的真实数据进行分析。"),
                    ("human", "{analysis_request}")
                ])
                
                analysis_chain = analysis_prompt_template | llm
                analysis_result = analysis_chain.invoke({"analysis_request": analysis_prompt})
                
                if hasattr(analysis_result, 'content'):
                    report = analysis_result.content
                else:
                    report = str(analysis_result)
                    
                print(f"📊 [基本面分析师] 强制工具调用完成，报告长度: {len(report)}")
                
            except Exception as e:
                print(f"❌ [DEBUG] 强制工具调用分析失败: {e}")
                report = f"基本面分析失败：{str(e)}"
            
            return {"fundamentals_report": report}

        # 这里不应该到达，但作为备用
        print(f"📊 [DEBUG] 返回状态: fundamentals_report长度={len(result.content) if hasattr(result, 'content') else 0}")
        return {"messages": [result]}

    return fundamentals_analyst_node
