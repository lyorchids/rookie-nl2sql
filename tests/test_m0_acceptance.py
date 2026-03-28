"""
M0 Acceptance Test Script
验收标准: 输入一句话,控制台能正确打印意图对象
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from graphs.base_graph import run_query


def test_m0_acceptance():
    """
    M0 验收测试
    """
    print("="*70)
    print("M0 验收测试 - 项目脚手架与基线")
    print("="*70)

    # 测试用例
    test_cases = [
        {
            "id": 1,
            "question": "查询所有用户的订单数量",
            "expected_intent_type": "query"
        },
        {
            "id": 2,
            "question": "What are the top 10 customers?",
            "expected_intent_type": "query"
        },
        {
            "id": 3,
            "question": "统计每月销售额",
            "expected_intent_type": "query"
        }
    ]

    passed = 0
    failed = 0

    for test_case in test_cases:
        print(f"\n{'='*70}")
        print(f"测试用例 {test_case['id']}: {test_case['question']}")
        print(f"{'='*70}")

        try:
            result = run_query(test_case['question'])

            # 验证结果
            checks = {
                "question存在": result.get("question") is not None,
                "session_id存在": result.get("session_id") is not None,
                "timestamp存在": result.get("timestamp") is not None,
                "intent存在": result.get("intent") is not None,
                "intent包含type": result.get("intent", {}).get("type") is not None,
                "intent.type正确": result.get("intent", {}).get("type") == test_case["expected_intent_type"]
            }

            all_passed = all(checks.values())

            print(f"\n验收检查:")
            for check_name, check_result in checks.items():
                status = "✓" if check_result else "✗"
                print(f"  {status} {check_name}")

            if all_passed:
                print(f"\n✓ 测试用例 {test_case['id']} 通过")
                passed += 1
            else:
                print(f"\n✗ 测试用例 {test_case['id']} 失败")
                failed += 1

        except Exception as e:
            print(f"\n✗ 测试用例 {test_case['id']} 出错: {str(e)}")
            failed += 1

    # 输出总结
    print(f"\n{'='*70}")
    print("测试总结")
    print(f"{'='*70}")
    print(f"通过: {passed}/{len(test_cases)}")
    print(f"失败: {failed}/{len(test_cases)}")

    if passed == len(test_cases):
        print("\n🎉 恭喜! M0 验收测试全部通过!")
        print("✓ 基础State结构正常")
        print("✓ LangGraph图结构运行正常")
        print("✓ 意图解析功能正常")
        print("\n下一步: 切换到 01-prompt-nl2sql 分支,开始 M1 模块开发")
        return True
    else:
        print("\n⚠️  部分测试失败,请检查代码")
        return False


if __name__ == "__main__":
    success = test_m0_acceptance()
    sys.exit(0 if success else 1)