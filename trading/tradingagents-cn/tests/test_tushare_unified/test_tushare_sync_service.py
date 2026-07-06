"""
测试TushareSyncService
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from app.worker.tushare_sync_service import TushareSyncService


class TestTushareSyncService:
    """测试TushareSyncService类"""
    
    @pytest.fixture
    def sync_service(self):
        """创建TushareSyncService实例"""
        with patch('app.worker.tushare_sync_service.get_mongo_db') as mock_get_db, \
             patch('app.worker.tushare_sync_service.get_stock_data_service') as mock_get_service:

            # 模拟数据库和服务
            mock_get_db.return_value = Mock()
            mock_get_service.return_value = Mock()

            service = TushareSyncService()

            # 模拟初始化
            service.provider = Mock()
            service.provider.is_available.return_value = True

            return service
    
    @pytest.fixture
    def mock_stock_list(self):
        """模拟股票列表数据"""
        return [
            {
                "code": "000001",
                "name": "平安银行",
                "symbol": "000001",
                "full_symbol": "000001.SZ",
                "industry": "银行",
                "market_info": {"market": "CN", "exchange": "SZSE"},
                "data_source": "tushare",
                "updated_at": datetime.utcnow()
            },
            {
                "code": "000002",
                "name": "万科A",
                "symbol": "000002",
                "full_symbol": "000002.SZ",
                "industry": "全国地产",
                "market_info": {"market": "CN", "exchange": "SZSE"},
                "data_source": "tushare",
                "updated_at": datetime.utcnow()
            }
        ]
    
    @pytest.mark.asyncio
    async def test_initialize_success(self, sync_service):
        """测试初始化成功"""
        sync_service.provider.connect = AsyncMock(return_value=True)
        
        await sync_service.initialize()
        
        sync_service.provider.connect.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_initialize_failure(self, sync_service):
        """测试初始化失败"""
        sync_service.provider.connect = AsyncMock(return_value=False)
        
        with pytest.raises(RuntimeError, match="Tushare连接失败"):
            await sync_service.initialize()
    
    @pytest.mark.asyncio
    async def test_sync_stock_basic_info_success(self, sync_service, mock_stock_list):
        """测试同步股票基础信息成功"""
        # 模拟获取股票列表
        sync_service.provider.get_stock_list = AsyncMock(return_value=mock_stock_list)
        
        # 模拟批量处理
        sync_service._process_basic_info_batch = AsyncMock(return_value={
            "success_count": 2,
            "error_count": 0,
            "skipped_count": 0,
            "errors": []
        })
        
        result = await sync_service.sync_stock_basic_info()
        
        assert result["total_processed"] == 2
        assert result["success_count"] == 2
        assert result["error_count"] == 0
        assert "duration" in result
        sync_service.provider.get_stock_list.assert_called_once_with(market="CN")
    
    @pytest.mark.asyncio
    async def test_sync_stock_basic_info_no_data(self, sync_service):
        """测试同步股票基础信息无数据"""
        sync_service.provider.get_stock_list = AsyncMock(return_value=None)
        
        result = await sync_service.sync_stock_basic_info()
        
        assert result["total_processed"] == 0
        assert result["success_count"] == 0
        assert result["error_count"] == 0
    
    @pytest.mark.asyncio
    async def test_process_basic_info_batch_success(self, sync_service, mock_stock_list):
        """测试处理基础信息批次成功"""
        # 模拟数据库操作
        sync_service.stock_service.get_stock_basic_info = AsyncMock(return_value=None)
        sync_service.stock_service.update_stock_basic_info = AsyncMock(return_value=True)
        
        result = await sync_service._process_basic_info_batch(mock_stock_list, force_update=False)
        
        assert result["success_count"] == 2
        assert result["error_count"] == 0
        assert result["skipped_count"] == 0
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_process_basic_info_batch_skip_fresh_data(self, sync_service, mock_stock_list):
        """测试跳过新鲜数据"""
        # 模拟存在新鲜数据
        fresh_data = {"updated_at": datetime.utcnow()}
        sync_service.stock_service.get_stock_basic_info = AsyncMock(return_value=fresh_data)
        sync_service._is_data_fresh = Mock(return_value=True)
        
        result = await sync_service._process_basic_info_batch(mock_stock_list, force_update=False)
        
        assert result["success_count"] == 0
        assert result["error_count"] == 0
        assert result["skipped_count"] == 2
    
    @pytest.mark.asyncio
    async def test_sync_realtime_quotes_success(self, sync_service):
        """测试同步实时行情成功"""
        # 模拟数据库查询
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = [
            {"code": "000001"},
            {"code": "000002"}
        ]
        sync_service.db.stock_basic_info.find.return_value = mock_cursor
        
        # 模拟批量处理
        sync_service._process_quotes_batch = AsyncMock(return_value={
            "success_count": 2,
            "error_count": 0,
            "errors": []
        })
        
        result = await sync_service.sync_realtime_quotes()
        
        assert result["total_processed"] == 2
        assert result["success_count"] == 2
        assert result["error_count"] == 0
    
    @pytest.mark.asyncio
    async def test_process_quotes_batch_success(self, sync_service):
        """测试处理行情批次成功"""
        batch = ["000001", "000002"]
        
        # 模拟获取和保存行情
        sync_service._get_and_save_quotes = AsyncMock(return_value=True)
        
        result = await sync_service._process_quotes_batch(batch)
        
        assert result["success_count"] == 2
        assert result["error_count"] == 0
        assert len(result["errors"]) == 0
    
    @pytest.mark.asyncio
    async def test_get_and_save_quotes_success(self, sync_service):
        """测试获取并保存行情成功"""
        mock_quotes = {
            "code": "000001",
            "close": 12.60,
            "current_price": 12.60,
            "data_source": "tushare"
        }
        
        sync_service.provider.get_stock_quotes = AsyncMock(return_value=mock_quotes)
        sync_service.stock_service.update_market_quotes = AsyncMock(return_value=True)
        
        result = await sync_service._get_and_save_quotes("000001")
        
        assert result is True
        sync_service.provider.get_stock_quotes.assert_called_once_with("000001")
        sync_service.stock_service.update_market_quotes.assert_called_once_with("000001", mock_quotes)
    
    @pytest.mark.asyncio
    async def test_get_and_save_quotes_no_data(self, sync_service):
        """测试获取行情无数据"""
        sync_service.provider.get_stock_quotes = AsyncMock(return_value=None)
        
        result = await sync_service._get_and_save_quotes("000001")
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_sync_historical_data_success(self, sync_service):
        """测试同步历史数据成功"""
        # 模拟数据库查询
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = [
            {"code": "000001"},
            {"code": "000002"}
        ]
        sync_service.db.stock_basic_info.find.return_value = mock_cursor
        
        # 模拟获取历史数据
        import pandas as pd
        mock_df = pd.DataFrame({
            'date': ['2024-12-01'],
            'close': [12.60],
            'volume': [1000000]
        })
        sync_service.provider.get_historical_data = AsyncMock(return_value=mock_df)
        sync_service._save_historical_data = AsyncMock(return_value=1)
        sync_service._get_last_sync_date = AsyncMock(return_value='2024-11-01')
        
        result = await sync_service.sync_historical_data(incremental=True)
        
        assert result["total_processed"] == 2
        assert result["success_count"] == 2
        assert result["total_records"] == 2
        assert result["error_count"] == 0
    
    @pytest.mark.asyncio
    async def test_sync_financial_data_success(self, sync_service):
        """测试同步财务数据成功"""
        # 模拟数据库查询
        mock_cursor = AsyncMock()
        mock_cursor.__aiter__.return_value = [
            {"code": "000001"},
            {"code": "000002"}
        ]
        sync_service.db.stock_basic_info.find.return_value = mock_cursor
        
        # 模拟获取财务数据
        mock_financial_data = {
            "symbol": "000001",
            "revenue": 1000000,
            "net_income": 100000,
            "data_source": "tushare"
        }
        sync_service.provider.get_financial_data = AsyncMock(return_value=mock_financial_data)
        sync_service._save_financial_data = AsyncMock(return_value=True)
        
        result = await sync_service.sync_financial_data()
        
        assert result["total_processed"] == 2
        assert result["success_count"] == 2
        assert result["error_count"] == 0
    
    def test_is_data_fresh(self, sync_service):
        """测试数据新鲜度检查"""
        # 测试新鲜数据
        fresh_time = datetime.utcnow() - timedelta(hours=1)
        assert sync_service._is_data_fresh(fresh_time, hours=24) is True
        
        # 测试过期数据
        old_time = datetime.utcnow() - timedelta(hours=25)
        assert sync_service._is_data_fresh(old_time, hours=24) is False
        
        # 测试None
        assert sync_service._is_data_fresh(None, hours=24) is False
    
    @pytest.mark.asyncio
    async def test_get_sync_status_success(self, sync_service):
        """测试获取同步状态成功"""
        # 模拟数据库查询
        sync_service.db.stock_basic_info.count_documents = AsyncMock(return_value=5000)
        sync_service.db.market_quotes.count_documents = AsyncMock(return_value=5000)
        
        sync_service.db.stock_basic_info.find_one = AsyncMock(return_value={
            "updated_at": datetime.utcnow()
        })
        sync_service.db.market_quotes.find_one = AsyncMock(return_value={
            "updated_at": datetime.utcnow()
        })
        
        result = await sync_service.get_sync_status()
        
        assert result["provider_connected"] is True
        assert result["collections"]["stock_basic_info"]["count"] == 5000
        assert result["collections"]["market_quotes"]["count"] == 5000
        assert "status_time" in result
