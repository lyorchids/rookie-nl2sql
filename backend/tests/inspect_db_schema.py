"""
数据库Schema检查脚本
用于分析chinook.db数据库的结构，为Schema理解功能提供基础数据
"""
import sqlite3
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def get_database_connection():
    """获取数据库连接"""
    db_path = project_root / "data" / "chinook.db"
    if not db_path.exists():
        raise FileNotFoundError(f"数据库文件不存在: {db_path}")
    
    print(f"✓ 连接到数据库: {db_path}")
    return sqlite3.connect(str(db_path))


def get_all_tables(conn) -> List[str]:
    """获取所有表名"""
    cursor = conn.cursor()
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' 
        ORDER BY name
    """)
    tables = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return tables


def get_table_schema(conn, table_name: str) -> Dict[str, Any]:
    """获取表结构信息"""
    cursor = conn.cursor()
    
    # 获取字段信息
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns_info = cursor.fetchall()
    
    columns = []
    for col in columns_info:
        col_id, name, dtype, notnull, default_val, pk = col
        columns.append({
            "name": name,
            "type": dtype,
            "not_null": bool(notnull),
            "default": default_val,
            "primary_key": bool(pk)
        })
    
    # 获取外键信息
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    foreign_keys = cursor.fetchall()
    
    foreign_key_list = []
    for fk in foreign_keys:
        foreign_key_list.append({
            "id": fk[0],
            "seq": fk[1],
            "table": fk[2],  # 引用的表
            "from": fk[3],   # 本表的字段
            "to": fk[4],     # 引用表的字段
            "on_update": fk[5],
            "on_delete": fk[6],
            "match": fk[7]
        })
    
    cursor.close()
    
    return {
        "table_name": table_name,
        "columns": columns,
        "foreign_keys": foreign_key_list,
        "column_count": len(columns)
    }


def analyze_table_relationships(conn, tables: List[str]) -> Dict[str, List[Dict]]:
    """分析表之间的关系"""
    relationships = defaultdict(list)
    
    for table in tables:
        schema = get_table_schema(conn, table)
        for fk in schema["foreign_keys"]:
            relationships[table].append({
                "from_table": table,
                "from_column": fk["from"],
                "to_table": fk["table"],
                "to_column": fk["to"]
            })
    
    return dict(relationships)


def get_sample_data(conn, table_name: str, limit: int = 3) -> Tuple[List[str], List[Dict]]:
    """获取表的样本数据"""
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM {table_name} LIMIT {limit}")
    
    columns = [desc[0] for desc in cursor.description]
    rows = cursor.fetchall()
    
    # 转换为字典列表
    sample_data = []
    for row in rows:
        row_dict = {}
        for i, col in enumerate(columns):
            row_dict[col] = row[i]
        sample_data.append(row_dict)
    
    cursor.close()
    return columns, sample_data


def analyze_column_patterns(tables_info: List[Dict]) -> Dict[str, List[str]]:
    """分析字段名模式，用于生成描述"""
    patterns = defaultdict(list)
    
    for table_info in tables_info:
        table_name = table_info["table_name"]
        for column in table_info["columns"]:
            col_name = column["name"].lower()
            
            # 分析常见模式
            if col_name.endswith('_id'):
                patterns['id_fields'].append(f"{table_name}.{column['name']}")
            elif col_name.endswith('_date'):
                patterns['date_fields'].append(f"{table_name}.{column['name']}")
            elif col_name.endswith('_amount') or col_name.endswith('_price'):
                patterns['money_fields'].append(f"{table_name}.{column['name']}")
            elif col_name.endswith('_name'):
                patterns['name_fields'].append(f"{table_name}.{column['name']}")
            elif col_name.endswith('_count') or col_name.endswith('_total'):
                patterns['aggregate_fields'].append(f"{table_name}.{column['name']}")
            elif 'email' in col_name:
                patterns['email_fields'].append(f"{table_name}.{column['name']}")
            elif 'phone' in col_name:
                patterns['phone_fields'].append(f"{table_name}.{column['name']}")
            elif col_name in ['created_at', 'updated_at', 'timestamp']:
                patterns['timestamp_fields'].append(f"{table_name}.{column['name']}")
    
    return dict(patterns)


def generate_table_descriptions(tables_info: List[Dict]) -> Dict[str, str]:
    """生成表的自然语言描述"""
    descriptions = {}
    
    # 基于表名和字段信息推断描述
    for table_info in tables_info:
        table_name = table_info["table_name"]
        columns = table_info["columns"]
        column_names = [col["name"].lower() for col in columns]
        
        # 基于表名的常见模式
        if table_name.lower() in ['customers', 'customer']:
            descriptions[table_name] = "客户信息表，存储客户的基本资料和联系信息"
        elif table_name.lower() in ['employees', 'employee']:
            descriptions[table_name] = "员工信息表，存储员工的基本信息和工作详情"
        elif table_name.lower() in ['invoices', 'invoice']:
            descriptions[table_name] = "发票表，记录交易发票信息"
        elif table_name.lower() in ['items']:
            descriptions[table_name] = "发票明细表，记录发票中的具体项目"
        elif table_name.lower() in ['genres']:
            descriptions[table_name] = "音乐流派表，存储音乐流派分类信息"
        elif table_name.lower() in ['artists']:
            descriptions[table_name] = "艺术家表，存储音乐艺术家信息"
        elif table_name.lower() in ['albums']:
            descriptions[table_name] = "专辑表，存储音乐专辑信息"
        elif table_name.lower() in ['tracks']:
            descriptions[table_name] = "音轨表，存储音乐音轨信息"
        elif table_name.lower() in ['media_types']:
            descriptions[table_name] = "媒体类型表，存储音乐媒体格式类型"
        elif table_name.lower() in ['playlists']:
            descriptions[table_name] = "播放列表表，存储用户播放列表信息"
        elif table_name.lower() in ['playlist_track']:
            descriptions[table_name] = "播放列表关联表，记录播放列表与音轨的关联关系"
        else:
            # 基于字段信息推断
            if any('customer' in col.lower() for col in column_names):
                descriptions[table_name] = "与客户相关的数据表"
            elif any('employee' in col.lower() for col in column_names):
                descriptions[table_name] = "与员工相关的数据表"
            elif any('invoice' in col.lower() for col in column_names):
                descriptions[table_name] = "与发票相关的数据表"
            elif any('track' in col.lower() for col in column_names):
                descriptions[table_name] = "与音轨相关的数据表"
            else:
                descriptions[table_name] = f"{table_name}表"
    
    return descriptions


def generate_column_descriptions(table_name: str, columns: List[Dict]) -> Dict[str, str]:
    """生成字段的自然语言描述"""
    descriptions = {}
    
    for column in columns:
        col_name = column["name"].lower()
        col_type = column["type"].upper()
        
        # 基于字段名的常见模式
        if col_name == 'customerid' or col_name == 'customer_id':
            descriptions[column["name"]] = "客户唯一标识符"
        elif col_name == 'employeeid' or col_name == 'employee_id':
            descriptions[column["name"]] = "员工唯一标识符"
        elif col_name == 'invoiceid' or col_name == 'invoice_id':
            descriptions[column["name"]] = "发票唯一标识符"
        elif col_name == 'trackid' or col_name == 'track_id':
            descriptions[column["name"]] = "音轨唯一标识符"
        elif col_name == 'albumid' or col_name == 'album_id':
            descriptions[column["name"]] = "专辑唯一标识符"
        elif col_name == 'artistid' or col_name == 'artist_id':
            descriptions[column["name"]] = "艺术家唯一标识符"
        elif col_name == 'genreid' or col_name == 'genre_id':
            descriptions[column["name"]] = "流派唯一标识符"
        elif col_name == 'mediatypeid' or col_name == 'media_type_id':
            descriptions[column["name"]] = "媒体类型唯一标识符"
        elif col_name == 'playlistid' or col_name == 'playlist_id':
            descriptions[column["name"]] = "播放列表唯一标识符"
        
        elif col_name in ['firstname', 'first_name']:
            descriptions[column["name"]] = "名字"
        elif col_name in ['lastname', 'last_name']:
            descriptions[column["name"]] = "姓氏"
        elif col_name == 'email':
            descriptions[column["name"]] = "电子邮箱地址"
        elif col_name == 'phone':
            descriptions[column["name"]] = "电话号码"
        elif col_name == 'fax':
            descriptions[column["name"]] = "传真号码"
        elif col_name == 'address':
            descriptions[column["name"]] = "地址"
        elif col_name == 'city':
            descriptions[column["name"]] = "城市"
        elif col_name == 'state':
            descriptions[column["name"]] = "州/省"
        elif col_name == 'country':
            descriptions[column["name"]] = "国家"
        elif col_name == 'postalcode' or col_name == 'postal_code':
            descriptions[column["name"]] = "邮政编码"
        
        elif col_name == 'birthdate' or col_name == 'birth_date':
            descriptions[column["name"]] = "出生日期"
        elif col_name == 'hiredate' or col_name == 'hire_date':
            descriptions[column["name"]] = "雇佣日期"
        elif col_name == 'invoicedate' or col_name == 'invoice_date':
            descriptions[column["name"]] = "发票日期"
        elif col_name == 'releasedate' or col_name == 'release_date':
            descriptions[column["name"]] = "发布日期"
        
        elif col_name == 'unitprice' or col_name == 'unit_price':
            descriptions[column["name"]] = "单价"
        elif col_name == 'total' or col_name == 'totalamount':
            descriptions[column["name"]] = "总金额"
        elif col_name == 'milliseconds':
            descriptions[column["name"]] = "时长（毫秒）"
        elif col_name == 'bytes':
            descriptions[column["name"]] = "文件大小（字节）"
        elif col_name == 'composer':
            descriptions[column["name"]] = "作曲家"
        
        elif col_name == 'title':
            descriptions[column["name"]] = "标题/名称"
        elif col_name == 'name':
            descriptions[column["name"]] = "名称"
        elif col_name == 'levelname' or col_name == 'level':
            descriptions[column["name"]] = "级别/层级"
        elif col_name == 'reports_to' or col_name == 'reportsto':
            descriptions[column["name"]] = "上级领导ID"
        
        elif col_name.endswith('_id'):
            # 通用ID字段
            entity = col_name.replace('_id', '').replace('id', '')
            if entity:
                descriptions[column["name"]] = f"{entity}唯一标识符"
            else:
                descriptions[column["name"]] = "唯一标识符"
        
        elif 'date' in col_name:
            descriptions[column["name"]] = "日期时间"
        
        elif 'count' in col_name:
            descriptions[column["name"]] = "数量"
        
        else:
            # 默认描述
            descriptions[column["name"]] = column["name"]
    
    return descriptions


def format_enhanced_schema_string(tables_info: List[Dict], 
                                 table_descriptions: Dict[str, str],
                                 relationships: Dict[str, List[Dict]]) -> str:
    """格式化增强的schema字符串"""
    
    schema_lines = []
    schema_lines.append("=" * 70)
    schema_lines.append("数据库Schema（含描述增强）")
    schema_lines.append("=" * 70)
    
    for i, table_info in enumerate(tables_info, 1):
        table_name = table_info["table_name"]
        columns = table_info["columns"]
        
        # 表描述
        table_desc = table_descriptions.get(table_name, table_name)
        
        schema_lines.append(f"\n{i}. {table_name} ({table_desc})")
        schema_lines.append("-" * 50)
        
        # 字段描述
        column_descriptions = generate_column_descriptions(table_name, columns)
        
        for col in columns:
            col_desc = column_descriptions.get(col["name"], col["name"])
            col_type = col["type"]
            
            # 标记主键和外键
            markers = []
            if col["primary_key"]:
                markers.append("主键")
            if col["not_null"]:
                markers.append("非空")
            
            marker_str = f" ({', '.join(markers)})" if markers else ""
            
            schema_lines.append(f"  • {col['name']}: {col_type}{marker_str} - {col_desc}")
    
    # 添加关系说明
    if relationships:
        schema_lines.append("\n" + "=" * 70)
        schema_lines.append("表关系说明")
        schema_lines.append("=" * 70)
        
        for table, rels in relationships.items():
            for rel in rels:
                schema_lines.append(
                    f"• {rel['from_table']}.{rel['from_column']} → "
                    f"{rel['to_table']}.{rel['to_column']}"
                )
    
    return "\n".join(schema_lines)


def main():
    """主函数"""
    print("=" * 70)
    print("数据库Schema检查工具")
    print("=" * 70)
    print()
    
    try:
        # 1. 连接数据库
        conn = get_database_connection()
        
        # 2. 获取所有表
        tables = get_all_tables(conn)
        print(f"\n📊 数据库包含 {len(tables)} 个表:")
        for table in tables:
            print(f"  • {table}")
        
        # 3. 获取每个表的结构
        tables_info = []
        for table in tables:
            schema = get_table_schema(conn, table)
            tables_info.append(schema)
            
            print(f"\n📋 表: {table}")
            print(f"   字段数量: {schema['column_count']}")
            print(f"   外键数量: {len(schema['foreign_keys'])}")
            
            # 显示字段信息
            print("   字段列表:")
            for col in schema['columns']:
                pk = " (PK)" if col['primary_key'] else ""
                fk = " (FK)" if any(fk['from'] == col['name'] for fk in schema['foreign_keys']) else ""
                print(f"     - {col['name']}: {col['type']}{pk}{fk}")
        
        # 4. 分析表关系
        print("\n" + "=" * 70)
        print("🔗 表关系分析")
        print("=" * 70)
        
        relationships = analyze_table_relationships(conn, tables)
        for table, rels in relationships.items():
            if rels:
                print(f"\n表 {table} 的外键关系:")
                for rel in rels:
                    print(f"  • {rel['from_column']} → {rel['to_table']}.{rel['to_column']}")
        
        # 5. 分析字段模式
        print("\n" + "=" * 70)
        print("🔍 字段模式分析")
        print("=" * 70)
        
        patterns = analyze_column_patterns(tables_info)
        for pattern_name, fields in patterns.items():
            print(f"\n{pattern_name}:")
            for field in fields[:5]:  # 只显示前5个
                print(f"  • {field}")
            if len(fields) > 5:
                print(f"  ... 还有 {len(fields) - 5} 个")
        
        # 6. 生成表描述
        print("\n" + "=" * 70)
        print("📝 表描述生成")
        print("=" * 70)
        
        table_descriptions = generate_table_descriptions(tables_info)
        for table_name, desc in table_descriptions.items():
            print(f"{table_name}: {desc}")
        
        # 7. 生成增强的schema字符串
        print("\n" + "=" * 70)
        print("🎯 增强Schema（用于LLM提示词）")
        print("=" * 70)
        
        enhanced_schema = format_enhanced_schema_string(
            tables_info, table_descriptions, relationships
        )
        print(enhanced_schema)  # 完整显示
        
        # 8. 保存增强的schema到文件
        schema_file_path = project_root / "data" / "enhanced_schema.txt"
        with open(schema_file_path, "w", encoding="utf-8") as f:
            f.write(enhanced_schema)
        print(f"\n✅ 增强的Schema已保存到: {schema_file_path}")
        
        # 9. 获取样本数据
        print("\n" + "=" * 70)
        print("📊 样本数据示例")
        print("=" * 70)
        
        for table in tables[:2]:  # 只显示前2个表的样本
            columns, sample_data = get_sample_data(conn, table, limit=2)
            print(f"\n表: {table}")
            print(f"列: {', '.join(columns[:6])}")  # 只显示前6列
            for row in sample_data[:2]:
                # 只显示前6列
                values = [str(row.get(col, ''))[:20] for col in columns[:6]]
                print(f"  {values}")
        
        conn.close()
        
        print("\n" + "=" * 70)
        print("✅ 数据库Schema检查完成!")
        print("=" * 70)
        
        # 返回有用的信息供后续使用
        return {
            "tables_count": len(tables),
            "tables_info": tables_info,
            "relationships": relationships,
            "patterns": patterns,
            "table_descriptions": table_descriptions
        }
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = main()
    
    if result:
        print(f"\n总结:")
        print(f"- 表数量: {result['tables_count']}")
        print(f"- 有外键关系的表: {len(result['relationships'])}")
        print(f"- 字段模式类型: {len(result['patterns'])}")