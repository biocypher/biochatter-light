import streamlit as st
from biochatter.llm_connect.available_models import (
    GEMINI_MODELS,
    OPENAI_MODELS,
)

ss = st.session_state

from .handlers import _change_model


def model_select():
    """Select the primary model to use for the conversation."""
    with st.expander("Model selection", expanded=False):
        if ss.mode not in ["getting_key", "getting_name"]:
            st.markdown("Please reload the app to change the model.")
            return

        if ss.user == "community":
            st.warning("You are currently using the community key. Please reload the app to change the model.")
            return

        # concatenate GEMINI_MODELS and OPENAI_MODELS
        models = GEMINI_MODELS + OPENAI_MODELS  # + HUGGINGFACE_MODELS  + XINFERENCE_MODELS

        # Find the index of the current primary model, default to 0 if not found
        try:
            current_model_index = models.index(ss.primary_model)
        except (ValueError, AttributeError):
            current_model_index = 0

        st.selectbox(
            "Primary model",
            options=models,
            index=current_model_index,
            on_change=_change_model,
            key="_primary_model",
            help=(
                "This is the model you will be talking to. Caution: changing the model will reset your conversation."
            ),
        )

        if ss.primary_model == "custom-endpoint":
            # ask for base url of endpoint, target is ss.xinference_base_url,
            # default value is also ss.xinference_base_url
            ss.xinference_base_url = st.text_input(
                "Base URL:",
                value=ss.xinference_base_url,
                help=("Please enter the base URL of your custom XInference endpoint."),
            )
