"""检查用户数据"""
from pymongo import MongoClient
from bson import ObjectId

client = MongoClient('mongodb://admin:tradingagents123@localhost:27017/')
db = client['tradingagents']

user_id = '68a1edf6b2c2b49285449e20'

print(f"检查用户ID: {user_id}")
print(f"是否是有效的ObjectId: {ObjectId.is_valid(user_id)}")

# 检查 user_favorites 集合
print(f"\n检查 user_favorites 集合:")
user_fav_doc = db.user_favorites.find_one({"user_id": user_id})
if user_fav_doc:
    print(f"✅ 在 user_favorites 集合中找到用户")
    print(f"   favorites数量: {len(user_fav_doc.get('favorites', []))}")
    print(f"   favorites: {user_fav_doc.get('favorites', [])}")
else:
    print(f"❌ 在 user_favorites 集合中未找到用户")

print(f"\nuser_favorites 集合中的所有文档:")
all_fav_docs = list(db.user_favorites.find({}))
print(f"共 {len(all_fav_docs)} 个文档")
for doc in all_fav_docs:
    print(f"  - user_id: {doc.get('user_id')}")
    print(f"    favorites数量: {len(doc.get('favorites', []))}")

try:
    oid = ObjectId(user_id)
    print(f"ObjectId转换成功: {oid}")
    print(f"ObjectId类型: {type(oid)}")

    # 查找所有用户
    all_users = list(db.users.find({}, {'_id': 1, 'username': 1}))
    print(f"\n数据库中的所有用户 (共{len(all_users)}个):")
    for u in all_users:
        print(f"  - _id: {u['_id']} (类型: {type(u['_id'])})")
        print(f"    username: {u.get('username', 'N/A')}")
        print(f"    _id == oid: {u['_id'] == oid}")
        print(f"    str(_id) == user_id: {str(u['_id']) == user_id}")
        print()

    # 尝试不同的查询方式
    print("\n尝试不同的查询方式:")

    # 方式1: 使用ObjectId
    user1 = db.users.find_one({'_id': oid})
    print(f"1. 使用ObjectId查询: {user1 is not None}")

    # 方式2: 使用字符串
    user2 = db.users.find_one({'_id': user_id})
    print(f"2. 使用字符串查询: {user2 is not None}")

    # 方式3: 查询所有然后过滤
    user3 = None
    for u in all_users:
        if str(u['_id']) == user_id:
            user3 = db.users.find_one({'_id': u['_id']})
            break
    print(f"3. 先列表后查询: {user3 is not None}")

    if user3:
        print(f"\n✅ 找到用户")
        print(f"   用户名: {user3.get('username')}")
        print(f"   邮箱: {user3.get('email')}")
        print(f"   有favorite_stocks字段: {'favorite_stocks' in user3}")
        if 'favorite_stocks' in user3:
            print(f"   favorite_stocks类型: {type(user3['favorite_stocks'])}")
            print(f"   favorite_stocks长度: {len(user3['favorite_stocks'])}")
        else:
            print(f"   需要初始化favorite_stocks字段")

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()

