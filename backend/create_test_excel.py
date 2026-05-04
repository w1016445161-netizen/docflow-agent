import pandas as pd

data = {
    "姓名": ["张三", "李四", "王五", "赵六", "钱七"],
    "课程": ["Python", "数据分析", "AI应用", "前端开发", "机器学习"],
    "成绩": [88, 92, 85, 79, 95],
    "学习时长": [12, 15, 10, 8, 18],
}

df = pd.DataFrame(data)

df.to_excel("test_students.xlsx", index=False)

print("测试 Excel 已生成：test_students.xlsx")
