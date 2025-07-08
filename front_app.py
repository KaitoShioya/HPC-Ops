import streamlit as st
import json
import os


def get_input_widget(param_type, key, default_value=None):
    """型に応じた入力ウィジェットを返す"""
    if param_type == "str":
        return st.text_input("value", value=default_value or "", key=key)
    elif param_type == "int":
        return st.number_input("value", value=default_value or 0, step=1, key=key)
    elif param_type == "float":
        return st.number_input("value", value=default_value or 0.0, step=0.1, key=key)
    elif param_type == "list[str]":
        # テキストエリアで改行区切りの文字列リストを入力
        text_value = (
            default_value
            if isinstance(default_value, str)
            else "\n".join(default_value or [])
        )
        text_input = st.text_area(
            "value (newline delimiter)", value=text_value, key=key
        )
        return text_input.split("\n") if text_input else []
    elif param_type == "list[int]":
        # テキストエリアでカンマ区切りの数値リストを入力
        text_value = (
            default_value
            if isinstance(default_value, str)
            else ",".join(map(str, default_value or []))
        )
        text_input = st.text_input("value (comma delimiter)", value=text_value, key=key)
        try:
            return [int(x.strip()) for x in text_input.split(",") if x.strip()]
        except ValueError:
            st.error("整数をカンマ区切りで入力してください")
            return []
    elif param_type == "list[float]":
        # テキストエリアでカンマ区切りの浮動小数点リストを入力
        text_value = (
            default_value
            if isinstance(default_value, str)
            else ",".join(map(str, default_value or []))
        )
        text_input = st.text_input("value (comma delimiter)", value=text_value, key=key)
        try:
            return [float(x.strip()) for x in text_input.split(",") if x.strip()]
        except ValueError:
            st.error("数値をカンマ区切りで入力してください")
            return []


def main():
    # 新しいパラメータ追加フォーム
    st.subheader("Add new parameter")

    with st.form("add_param_form"):
        col1, col2, col3 = st.columns([0.3, 0.3, 0.3])

        with col1:
            new_param_name = st.text_input("Name")

        with col2:
            new_param_type = st.selectbox(
                "Object type",
                ["str", "list[str]", "int", "list[int]", "float", "list[float]"],
            )

        with col3:
            new_param_value = get_input_widget(new_param_type, "new_param_value")

        col_add, col_remove = st.columns(2)
        with col_add:
            add_button = st.form_submit_button("Add param")
        with col_remove:
            remove_button = st.form_submit_button("Remove param")

        if add_button and new_param_name:
            # 新しいパラメータを追加
            new_param = {
                "name": new_param_name,
                "type": new_param_type,
                "value": new_param_value,
            }
            st.session_state.parameters.append(new_param)
            st.success(f"Add '{new_param_name}'")
            st.rerun()

        if remove_button and st.session_state.parameters:
            # 最後のパラメータを削除
            removed_param = st.session_state.parameters.pop()
            st.success(f"Delete '{removed_param['name']}'")
            st.rerun()

    # 既存パラメータの表示と編集
    if st.session_state.parameters:
        st.subheader("Current Parameters")

        for i, param in enumerate(st.session_state.parameters):
            with st.container():
                st.write(f"**Parameter {i + 1}**")

                col1, col2, col3, col4 = st.columns([0.25, 0.25, 0.35, 0.15])

                with col1:
                    # パラメータ名の編集
                    updated_name = st.text_input(
                        "Name", value=param["name"], key=f"name_{i}"
                    )
                    st.session_state.parameters[i]["name"] = updated_name

                with col2:
                    # 型タイプの編集
                    type_options = [
                        "str",
                        "list[str]",
                        "int",
                        "list[int]",
                        "float",
                        "list[float]",
                    ]
                    current_type_index = (
                        type_options.index(param["type"])
                        if param["type"] in type_options
                        else 0
                    )
                    updated_type = st.selectbox(
                        "Object type",
                        type_options,
                        index=current_type_index,
                        key=f"type_{i}",
                    )
                    st.session_state.parameters[i]["type"] = updated_type

                with col3:
                    # 値の編集（型に応じて入力ウィジェットを変更）
                    updated_value = get_input_widget(
                        updated_type, f"value_{i}", param["value"]
                    )
                    st.session_state.parameters[i]["value"] = updated_value

                with col4:
                    # 個別削除ボタン
                    if st.button("Delete", key=f"delete_{i}"):
                        st.session_state.parameters.pop(i)
                        st.rerun()

                st.divider()

    # 現在の設定をJSON形式で表示
    if st.session_state.parameters:
        st.subheader("Current params (JSON)")
        config_dict = {
            param["name"]: param["value"] for param in st.session_state.parameters
        }
        st.json(config_dict)

        # JSONダウンロードボタン
        json_str = json.dumps(config_dict, ensure_ascii=False, indent=2)
        st.download_button(
            label="Download current params",
            data=json_str,
            file_name="config.json",
            mime="application/json",
        )


st.markdown("# HPC-Ops Web application :chart_with_upwards_trend:")
st.write("")
# wandbの実験粒度設定
st.markdown("## WandB Configuration :test_tube:")
st.markdown("### Project name")
project = st.text_input(
    label="wandb project name",
    value="*Required",
)
if project == "*Required":
    st.warning("This item is required")
st.write(project)
st.markdown("### Group name")
group = st.text_input(
    label="wandb group name",
    value="Option",
)
st.write(group)
st.markdown("### Jobtype name")
jobtype = st.text_input(
    label="wandb jobtype name",
    value="Option",
)
st.write(jobtype)
# flow logicの選択
# TODO: 選択したファイルを自動でwandbにアップロード
st.markdown("## Select your FlowLogic file :sparkles:")
flow_logic_dir = "flow_logics/"
flow_logic_file_list = [
    f
    for f in os.listdir(flow_logic_dir)
    if os.path.isfile(os.path.join(flow_logic_dir, f))
]
flow_logic_filename = st.selectbox(
    label="Experiments logic file", options=flow_logic_file_list
)
if flow_logic_filename is not None:
    flow_logic_dir = flow_logic_dir + flow_logic_filename
    flow_logic_name = flow_logic_filename.replace(".py", "")
else:
    st.error("You must select or add FlowLogic file ")
# スパコン設定
st.markdown("## HPC Configuration :rocket:")
st.markdown("### node")
node = st.number_input(
    label="Job node you can use",
    min_value=1,
    max_value=5,
    value=1,
)
st.write(node)
st.markdown("### vnode_core")
vnode_core = st.number_input(
    label="Job vnode_core you can use",
    min_value=1,
    max_value=120,
    value=1,
)
st.write(vnode_core)
st.markdown("### gpu")
gpu = st.number_input(
    label="Job gpu you can use",
    min_value=1,
    max_value=10,
    value=1,
)
st.markdown("### elapse")
elapse_hour = st.number_input(
    label="Job timeout limit",
    min_value=1,
    max_value=1000,
    value=1,
)
elapse = f"{elapse_hour}:00:00"
st.write(elapse)
# 実験パラメータ設定
st.markdown("## Parameters Configuration :wrench:")
# ページ設定
st.set_page_config(layout="wide")

# セッション状態の初期化
if "parameters" not in st.session_state:
    st.session_state.parameters = []

main()
