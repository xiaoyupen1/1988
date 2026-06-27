import streamlit as st
import plotly.figure_factory as ff
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import numpy as np

st.set_page_config(
    page_title="甘特图生成工具",
    page_icon="📊",
    layout="wide"
)

st.title("📊 甘特图生成工具")
st.markdown("---")

if 'tasks' not in st.session_state:
    st.session_state.tasks = []
if 'task_counter' not in st.session_state:
    st.session_state.task_counter = 0

def calculate_task_schedule(tasks: List[Dict], start_date: datetime) -> List[Dict]:
    scheduled_tasks = []
    task_end_times = {}
    
    for task in tasks:
        task_name = task['name']
        duration = task['duration']
        dependencies = task.get('dependencies', [])
        parallel_group = task.get('parallel_group', None)
        
        start_time = start_date
        
        for dep in dependencies:
            if dep in task_end_times:
                if task_end_times[dep] > start_time:
                    start_time = task_end_times[dep]
        
        if parallel_group:
            parallel_tasks = [t for t in tasks if t.get('parallel_group') == parallel_group]
            parallel_task_names = [t['name'] for t in parallel_tasks]
            
            for pt_name in parallel_task_names:
                if pt_name in task_end_times and pt_name != task_name:
                    if task_end_times[pt_name] > start_time:
                        start_time = task_end_times[pt_name]
        
        end_time = start_time + timedelta(days=duration)
        task_end_times[task_name] = end_time
        
        scheduled_tasks.append({
            'Task': task_name,
            'Start': start_time,
            'Finish': end_time,
            'Resource': task.get('resource', '默认')
        })
    
    return scheduled_tasks

def create_gantt_chart(scheduled_tasks: List[Dict]) -> go.Figure:
    if not scheduled_tasks:
        return None
    
    df = pd.DataFrame(scheduled_tasks)
    
    fig = ff.create_gantt(
        df,
        colors=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'],
        index_col='Resource',
        show_colorbar=True,
        group_tasks=True,
        showgrid_x=True,
        showgrid_y=True
    )
    
    fig.update_layout(
        title='项目甘特图',
        xaxis_title='日期',
        yaxis_title='任务',
        height=max(400, len(scheduled_tasks) * 40 + 100),
        font=dict(size=12)
    )
    
    return fig

with st.sidebar:
    st.header("⚙️ 全局设置")
    
    st.subheader("项目时间范围")
    start_date = st.date_input("项目开始日期", datetime.now())
    end_date = st.date_input("项目结束日期", datetime.now() + timedelta(days=30))
    
    st.markdown("---")
    st.subheader("添加新任务")
    
    with st.form("task_form"):
        task_name = st.text_input("任务名称", key="new_task_name")
        task_duration = st.number_input("任务时长（天）", min_value=1, value=1, key="new_task_duration")
        task_resource = st.selectbox(
            "任务资源/类别",
            ["开发", "测试", "设计", "部署", "文档", "其他"],
            key="new_task_resource"
        )
        
        existing_tasks = [t['name'] for t in st.session_state.tasks]
        dependencies = st.multiselect(
            "前置任务（依赖）",
            existing_tasks,
            key="new_task_dependencies"
        )
        
        parallel_group = st.text_input(
            "并行组（相同组名的任务将并行执行）",
            key="new_parallel_group"
        )
        
        submitted = st.form_submit_button("添加任务")
        
        if submitted and task_name:
            st.session_state.task_counter += 1
            new_task = {
                'id': st.session_state.task_counter,
                'name': task_name,
                'duration': task_duration,
                'resource': task_resource,
                'dependencies': dependencies,
                'parallel_group': parallel_group if parallel_group else None
            }
            st.session_state.tasks.append(new_task)
            st.success(f"任务 '{task_name}' 已添加！")

st.header("📋 任务列表")

if st.session_state.tasks:
    df_display = pd.DataFrame([
        {
            '任务名称': t['name'],
            '时长（天）': t['duration'],
            '资源': t['resource'],
            '前置任务': ', '.join(t['dependencies']) if t['dependencies'] else '无',
            '并行组': t['parallel_group'] if t['parallel_group'] else '无'
        }
        for t in st.session_state.tasks
    ])
    
    st.dataframe(df_display, use_container_width=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ 清空所有任务"):
            st.session_state.tasks = []
            st.session_state.task_counter = 0
            st.rerun()
    
    with col2:
        task_to_delete = st.selectbox(
            "选择要删除的任务",
            [t['name'] for t in st.session_state.tasks]
        )
        if st.button("删除选中任务"):
            st.session_state.tasks = [t for t in st.session_state.tasks if t['name'] != task_to_delete]
            st.rerun()
else:
    st.info("暂无任务，请在左侧添加任务")

st.markdown("---")
st.header("📊 甘特图")

if st.session_state.tasks:
    scheduled = calculate_task_schedule(st.session_state.tasks, datetime.combine(start_date, datetime.min.time()))
    fig = create_gantt_chart(scheduled)
    
    if fig:
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("📅 任务时间表")
        schedule_df = pd.DataFrame([
            {
                '任务': t['Task'],
                '开始日期': t['Start'].strftime('%Y-%m-%d'),
                '结束日期': t['Finish'].strftime('%Y-%m-%d'),
                '时长（天）': (t['Finish'] - t['Start']).days
            }
            for t in scheduled
        ])
        st.dataframe(schedule_df, use_container_width=True)
        
        csv = schedule_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button(
            label="📥 导出为 CSV",
            data=csv,
            file_name='gantt_chart.csv',
            mime='text/csv'
        )
else:
    st.info("请先添加任务以生成甘特图")

st.markdown("---")
st.header("💡 使用说明")
with st.expander("查看使用说明"):
    st.markdown("""
    ### 如何使用本工具
    
    1. **设置项目时间范围**：在左侧边栏设置项目的开始和结束日期
    
    2. **添加任务**：
       - 输入任务名称
       - 设置任务时长（天数）
       - 选择任务资源/类别
       - 选择前置任务（依赖关系）
       - 设置并行组（可选）
    
    3. **任务关系**：
       - **串行关系**：通过设置前置任务，任务将在前置任务完成后开始
       - **并行关系**：将多个任务设置为相同的并行组名，它们将同时开始
    
    4. **生成甘特图**：添加任务后，甘特图会自动生成
    
    5. **导出**：可以导出任务时间表为CSV文件
    
    ### 示例
    
    假设有一个软件开发项目：
    - 任务1：需求分析（5天）
    - 任务2：UI设计（3天），依赖任务1
    - 任务3：后端开发（7天），依赖任务1，与任务2并行
    - 任务4：前端开发（6天），依赖任务2和任务3
    - 任务5：测试（4天），依赖任务4
    
    你可以这样设置：
    - 添加任务1，时长5天
    - 添加任务2，时长3天，前置任务选择"需求分析"，并行组填写"开发阶段"
    - 添加任务3，时长7天，前置任务选择"需求分析"，并行组填写"开发阶段"
    - 添加任务4，时长6天，前置任务选择"UI设计"和"后端开发"
    - 添加任务5，时长4天，前置任务选择"前端开发"
    """)