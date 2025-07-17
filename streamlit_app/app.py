# -*- coding: utf-8 -*-

import streamlit as st
import time
from datetime import datetime
import sys
import os

# Add parent directory to path to import from main project
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from streamlit_app.appointment_workflow import AppointmentWorkflow
from config import LOCATIONS

# 配置页面
st.set_page_config(
    page_title="SuperC Termin Bot - 预约检查工具",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
<style>
    .step-container {
        border: 1px solid #ddd;
        border-radius: 5px;
        padding: 10px;
        margin: 5px 0;
        background-color: #f9f9f9;
    }
    .step-success {
        border-left: 4px solid #28a745;
        background-color: #d4edda;
    }
    .step-error {
        border-left: 4px solid #dc3545;
        background-color: #f8d7da;
    }
    .step-warning {
        border-left: 4px solid #ffc107;
        background-color: #fff3cd;
    }
    .step-info {
        border-left: 4px solid #17a2b8;
        background-color: #d1ecf1;
    }
    .step-pending {
        border-left: 4px solid #6c757d;
        background-color: #e2e3e5;
    }
</style>
""", unsafe_allow_html=True)

def render_step_node(step_info, is_current=False):
    """
    渲染单个步骤节点
    """
    status = step_info.get("status", "pending")
    title = step_info.get("title", "未知步骤")
    message = step_info.get("message", "")
    details = step_info.get("details", "")
    
    # 选择样式类
    css_class = f"step-{status}"
    if is_current:
        css_class += " step-current"
    
    # 状态图标
    status_icons = {
        "success": "✅",
        "error": "❌", 
        "warning": "⚠️",
        "info": "ℹ️",
        "pending": "⏳"
    }
    icon = status_icons.get(status, "⚪")
    
    # 渲染步骤
    st.markdown(f"""
    <div class="step-container {css_class}">
        <h4>{icon} 步骤 {step_info.get('step', 'N/A')}: {title}</h4>
        <p><strong>状态:</strong> {message}</p>
        {f'<p><strong>详情:</strong> {details}</p>' if details else ''}
        {f'<p><strong>URL:</strong> <code>{step_info.get("url", "")}</code></p>' if step_info.get("url") else ''}
    </div>
    """, unsafe_allow_html=True)

def main():
    st.title("🏥 SuperC Termin Bot - 预约检查工具")
    st.markdown("---")
    
    # 侧边栏配置
    st.sidebar.header("🔧 配置选项")
    
    # 选择地点
    location_options = {
        "SuperC": "superc",
        "Infostelle": "infostelle"
    }
    selected_location_name = st.sidebar.selectbox(
        "选择预约地点",
        options=list(location_options.keys()),
        index=0
    )
    selected_location = location_options[selected_location_name]
    
    # 显示当前配置
    st.sidebar.markdown("### 📋 当前配置")
    config = LOCATIONS[selected_location]
    st.sidebar.write(f"**地点:** {config['name']}")
    st.sidebar.write(f"**选择文本:** {config['selection_text']}")
    st.sidebar.write(f"**提交文本:** {config['submit_text'][:50]}...")
    
    # 主界面
    col1, col2 = st.columns([2, 3])
    
    with col1:
        st.header("🎯 操作面板")
        
        # 开始检查按钮
        if st.button("🚀 开始预约检查", type="primary", use_container_width=True):
            st.session_state.workflow_running = True
            st.session_state.workflow_steps = []
            st.session_state.workflow_result = None
        
        # 重置按钮
        if st.button("🔄 重置", use_container_width=True):
            for key in ['workflow_running', 'workflow_steps', 'workflow_result', 'workflow_message']:
                if key in st.session_state:
                    del st.session_state[key]
            st.rerun()
        
        # 状态信息
        st.markdown("### 📊 流程概览")
        st.markdown("""
        **预约检查流程包括以下步骤:**
        
        1. **步骤 1-2:** 获取初始页面
        2. **步骤 3:** 选择地点类型  
        3. **步骤 3:** 获取位置信息
        4. **步骤 4:** 提交位置信息
        5. **步骤 4:** 检查预约可用性
        
        ⚠️ **注意:** 此工具仅检查到步骤4，不会进行实际预约。
        """)
    
    with col2:
        st.header("📈 流程进度")
        
        # 执行工作流
        if st.session_state.get('workflow_running', False):
            # 创建进度条
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 初始化工作流
            workflow = AppointmentWorkflow(selected_location)
            
            status_text.text("正在初始化...")
            progress_bar.progress(10)
            time.sleep(0.5)
            
            # 执行工作流
            status_text.text("正在执行预约检查流程...")
            progress_bar.progress(30)
            
            try:
                success, message = workflow.run_workflow()
                st.session_state.workflow_steps = workflow.get_steps()
                st.session_state.workflow_result = success
                st.session_state.workflow_message = message
                
                progress_bar.progress(100)
                status_text.text("流程执行完成!")
                time.sleep(1)
                
                # 清除进度指示器
                progress_bar.empty()
                status_text.empty()
                
            except Exception as e:
                st.error(f"执行过程中出现错误: {str(e)}")
                progress_bar.empty()
                status_text.empty()
            
            # 标记工作流完成
            st.session_state.workflow_running = False
        
        # 显示结果
        if 'workflow_result' in st.session_state:
            # 总体结果
            if st.session_state.workflow_result:
                st.success(f"✅ 检查完成: {st.session_state.workflow_message}")
            else:
                st.info(f"ℹ️ 检查完成: {st.session_state.workflow_message}")
            
            # 显示详细步骤
            st.markdown("### 📋 详细步骤")
            
            steps = st.session_state.get('workflow_steps', [])
            for i, step in enumerate(steps):
                render_step_node(step, is_current=False)
            
            # 统计信息
            if steps:
                st.markdown("### 📊 执行统计")
                col_stat1, col_stat2, col_stat3 = st.columns(3)
                
                with col_stat1:
                    success_count = len([s for s in steps if s.get('status') == 'success'])
                    st.metric("成功步骤", success_count)
                
                with col_stat2:
                    error_count = len([s for s in steps if s.get('status') == 'error'])
                    st.metric("错误步骤", error_count)
                
                with col_stat3:
                    total_steps = len(steps)
                    st.metric("总步骤数", total_steps)
                
                # 找到可用预约数量
                for step in steps:
                    if 'available_count' in step:
                        st.metric("发现可用预约", step['available_count'], "个时间段")
                        break
    
    # 页脚信息
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        <p>🤖 SuperC Termin Bot - Streamlit 版本</p>
        <p>⚠️ 仅用于检查预约可用性，不进行实际预约</p>
        <p>🕒 最后更新: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()