"""
测试统一的TushareProvider
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, date
import pandas as pd

from tradingagents.dataflows.providers.tushare_provider import TushareProvider


class TestTushareProvider:
    """测试TushareProvider类"""
    
    @pytest.fixture
    def provider(self):
        """创建TushareProvider实例"""
        return TushareProvider()
    
    @pytest.fixture
    def mock_tushare_api(self):
        """模拟Tushare API"""
        mock_api = Mock()
        
        # 模拟stock_basic返回数据
        mock_basic_data = pd.DataFrame({
            'ts_code': ['000001.SZ', '000002.SZ'],
            'symbol': ['000001', '000002'],
            'name': ['平安银行', '万科A'],
            'area': ['深圳', '深圳'],
            'industry': ['银行', '全国地产'],
            'market': ['主板', '主板'],
            'exchange': ['SZSE', 'SZSE'],
            'list_date': ['19910403', '19910129'],
            'is_hs': ['S', 'S']
        })
        mock_api.stock_basic.return_value = mock_basic_data
        
        # 模拟daily返回数据
        mock_daily_data = pd.DataFrame({
            'ts_code': ['000001.SZ'],
            'trade_date': ['20241201'],
            'open': [12.50],
            'high': [12.80],
            'low': [12.30],
            'close': [12.60],
            'pre_close': [12.40],
            'change': [0.20],
            'pct_chg': [1.61],
            'vol': [1000000],
            'amount': [12600000]
        })
        mock_api.daily.return_value = mock_daily_data
        
        # 模拟daily_basic返回数据
        mock_basic_daily = pd.DataFrame({
            'ts_code': ['000001.SZ'],
            'total_mv': [250000],
            'circ_mv': [200000],
            'pe': [5.2],
            'pb': [0.8],
            'turnover_rate': [2.5]
        })
        mock_api.daily_basic.return_value = mock_basic_daily
        
        return mock_api
    
    @pytest.mark.asyncio
    async def test_connect_success(self, provider, mock_tushare_api):
        """测试连接成功"""
        with patch('tradingagents.dataflows.providers.tushare_provider.TUSHARE_AVAILABLE', True), \
             patch('tradingagents.dataflows.providers.tushare_provider.ts') as mock_ts, \
             patch.object(provider, 'config', {'token': 'test_token'}):
            
            mock_ts.pro_api.return_value = mock_tushare_api
            
            result = await provider.connect()
            
            assert result is True
            assert provider.connected is True
            assert provider.api is not None
            mock_ts.set_token.assert_called_once_with('test_token')
    
    @pytest.mark.asyncio
    async def test_connect_no_token(self, provider):
        """测试无token连接失败"""
        with patch('tradingagents.dataflows.providers.tushare_provider.TUSHARE_AVAILABLE', True), \
             patch.object(provider, 'config', {'token': ''}):
            
            result = await provider.connect()
            
            assert result is False
            assert provider.connected is False
    
    @pytest.mark.asyncio
    async def test_get_stock_list(self, provider, mock_tushare_api):
        """测试获取股票列表"""
        provider.connected = True
        provider.api = mock_tushare_api
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_tushare_api.stock_basic.return_value
            
            result = await provider.get_stock_list(market="CN")
            
            assert result is not None
            assert len(result) == 2
            assert result[0]['code'] == '000001'
            assert result[0]['name'] == '平安银行'
            assert result[0]['market_info']['market'] == 'CN'
            assert result[0]['market_info']['exchange'] == 'SZSE'
    
    @pytest.mark.asyncio
    async def test_get_stock_basic_info_single(self, provider, mock_tushare_api):
        """测试获取单个股票基础信息"""
        provider.connected = True
        provider.api = mock_tushare_api
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            # 返回单行数据
            single_stock_data = mock_tushare_api.stock_basic.return_value.iloc[:1]
            mock_to_thread.return_value = single_stock_data
            
            result = await provider.get_stock_basic_info('000001')
            
            assert result is not None
            assert result['code'] == '000001'
            assert result['name'] == '平安银行'
            assert result['industry'] == '银行'
            assert result['data_source'] == 'tushare'
    
    @pytest.mark.asyncio
    async def test_get_stock_quotes(self, provider, mock_tushare_api):
        """测试获取实时行情"""
        provider.connected = True
        provider.api = mock_tushare_api
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            # 模拟realtime_quote失败，回退到daily
            mock_to_thread.side_effect = [
                Exception("权限不足"),  # realtime_quote失败
                mock_tushare_api.daily.return_value,  # daily成功
                mock_tushare_api.daily_basic.return_value  # daily_basic成功
            ]
            
            result = await provider.get_stock_quotes('000001')
            
            assert result is not None
            assert result['code'] == '000001'
            assert result['close'] == 12.60
            assert result['current_price'] == 12.60
            assert result['pct_chg'] == 1.61
            assert result['pe'] == 5.2
            assert result['data_source'] == 'tushare'
    
    @pytest.mark.asyncio
    async def test_get_historical_data(self, provider, mock_tushare_api):
        """测试获取历史数据"""
        provider.connected = True
        provider.api = mock_tushare_api
        
        with patch('asyncio.to_thread', new_callable=AsyncMock) as mock_to_thread:
            mock_to_thread.return_value = mock_tushare_api.daily.return_value
            
            result = await provider.get_historical_data('000001', '2024-11-01', '2024-12-01')
            
            assert result is not None
            assert isinstance(result, pd.DataFrame)
            assert len(result) == 1
            assert 'volume' in result.columns  # 检查列重命名
    
    def test_normalize_ts_code(self, provider):
        """测试ts_code标准化"""
        # 测试已有后缀的代码
        assert provider._normalize_ts_code('000001.SZ') == '000001.SZ'
        
        # 测试上交所代码
        assert provider._normalize_ts_code('600000') == '600000.SH'
        assert provider._normalize_ts_code('688001') == '688001.SH'
        
        # 测试深交所代码
        assert provider._normalize_ts_code('000001') == '000001.SZ'
        assert provider._normalize_ts_code('300001') == '300001.SZ'
    
    def test_determine_market_info_from_ts_code(self, provider):
        """测试市场信息确定"""
        # 测试上交所
        market_info = provider._determine_market_info_from_ts_code('600000.SH')
        assert market_info['market'] == 'CN'
        assert market_info['exchange'] == 'SSE'
        assert market_info['exchange_name'] == '上海证券交易所'
        
        # 测试深交所
        market_info = provider._determine_market_info_from_ts_code('000001.SZ')
        assert market_info['market'] == 'CN'
        assert market_info['exchange'] == 'SZSE'
        assert market_info['exchange_name'] == '深圳证券交易所'
        
        # 测试北交所
        market_info = provider._determine_market_info_from_ts_code('830001.BJ')
        assert market_info['market'] == 'CN'
        assert market_info['exchange'] == 'BSE'
        assert market_info['exchange_name'] == '北京证券交易所'
    
    def test_standardize_basic_info(self, provider):
        """测试基础信息标准化"""
        raw_data = {
            'ts_code': '000001.SZ',
            'symbol': '000001',
            'name': '平安银行',
            'area': '深圳',
            'industry': '银行',
            'market': '主板',
            'list_date': '19910403',
            'is_hs': 'S'
        }
        
        result = provider.standardize_basic_info(raw_data)
        
        assert result['code'] == '000001'
        assert result['name'] == '平安银行'
        assert result['full_symbol'] == '000001.SZ'
        assert result['list_date'] == '1991-04-03'
        assert result['market_info']['exchange'] == 'SZSE'
        assert result['data_source'] == 'tushare'
        assert isinstance(result['updated_at'], datetime)
    
    def test_standardize_quotes(self, provider):
        """测试行情数据标准化"""
        raw_data = {
            'ts_code': '000001.SZ',
            'trade_date': '20241201',
            'close': 12.60,
            'open': 12.50,
            'high': 12.80,
            'low': 12.30,
            'vol': 1000000,
            'amount': 12600000,
            'pct_chg': 1.61,
            'pe': 5.2,
            'pb': 0.8
        }
        
        result = provider.standardize_quotes(raw_data)
        
        assert result['code'] == '000001'
        assert result['close'] == 12.60
        assert result['current_price'] == 12.60
        assert result['volume'] == 1000000
        assert result['pct_chg'] == 1.61
        assert result['trade_date'] == '2024-12-01'
        assert result['data_source'] == 'tushare'
    
    def test_format_date_output(self, provider):
        """测试日期格式化"""
        # 测试YYYYMMDD格式
        assert provider._format_date_output('19910403') == '1991-04-03'
        assert provider._format_date_output('20241201') == '2024-12-01'
        
        # 测试date对象
        test_date = date(2024, 12, 1)
        assert provider._format_date_output(test_date) == '2024-12-01'
        
        # 测试None
        assert provider._format_date_output(None) is None
        assert provider._format_date_output('') is None
    
    def test_convert_to_float(self, provider):
        """测试数值转换"""
        assert provider._convert_to_float(12.5) == 12.5
        assert provider._convert_to_float('12.5') == 12.5
        assert provider._convert_to_float('12') == 12.0
        assert provider._convert_to_float(None) is None
        assert provider._convert_to_float('') is None
        assert provider._convert_to_float('invalid') is None
