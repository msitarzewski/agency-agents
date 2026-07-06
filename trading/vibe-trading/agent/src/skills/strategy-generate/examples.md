# Strategy Generate — Examples

## Example 1: A-share dual MA crossover (tushare)

User: "用000001.SZ做双均线金叉策略，短期5日长期20日，回测2024年"

Tool call sequence:
1. load_skill("strategy-generate") → 获得工作流指引
2. write_file("config.json") → 配置标的/日期/参数
   ```json
   {"source": "tushare", "codes": ["000001.SZ"], "start_date": "2024-01-01", "end_date": "2024-12-31", "initial_cash": 1000000, "commission": 0.001, "extra_fields": null}
   ```
3. write_file("code/signal_engine.py") → 双均线策略代码
4. bash("python -c \"import ast; ast.parse(open('code/signal_engine.py').read()); print('OK')\"") → AST 语法检查
5. backtest(run_dir=...) → 执行回测（引擎内置）
6. read_file("artifacts/metrics.csv") → 查看结果，按评审标准判断
7. (如需修复) edit_file("code/signal_engine.py", ...) → backtest → read_file

## Example 2: US stock RSI strategy (yfinance)

User: "Build RSI strategy on AAPL, buy when RSI<30 sell when RSI>70, backtest 2024"

Tool call sequence:
1. load_skill("strategy-generate") → 获得工作流指引
2. write_file("config.json") → 配置
   ```json
   {"source": "yfinance", "codes": ["AAPL.US"], "start_date": "2024-01-01", "end_date": "2024-12-31", "initial_cash": 1000000, "commission": 0.001, "extra_fields": null}
   ```
3. write_file("code/signal_engine.py") → RSI 策略代码
4. bash("python -c \"import ast; ast.parse(open('code/signal_engine.py').read()); print('OK')\"") → AST 检查
5. backtest(run_dir=...) → 执行回测（引擎内置）
6. read_file("artifacts/metrics.csv") → 查看结果
7. (如需修复) edit_file → backtest → read_file

## Example 3: Crypto trend strategy (okx)

User: "BTC-USDT趋势跟踪策略，回测2024年"

Tool call sequence:
1. load_skill("strategy-generate") → 获得工作流指引
2. write_file("config.json") → 配置
   ```json
   {"source": "okx", "codes": ["BTC-USDT"], "start_date": "2024-01-01", "end_date": "2024-12-31", "initial_cash": 1000000, "commission": 0.001, "extra_fields": null}
   ```
3. write_file("code/signal_engine.py") → 趋势策略代码
4. bash("python -c \"import ast; ast.parse(open('code/signal_engine.py').read()); print('OK')\"") → AST 检查
5. backtest(run_dir=...) → 执行回测（引擎内置）
6. read_file("artifacts/metrics.csv") → 查看结果
7. (如需修复) edit_file → backtest → read_file
