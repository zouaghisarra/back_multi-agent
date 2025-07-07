import os
from pydantic import BaseModel, Field
from llama_cpp import Llama

class EnvConfig(BaseModel):
    model_path: str = Field(
        "C:/Users/HP/llama.cpp/models/Saul-7B-Instruct-v1.Q4_K_M.gguf",
        #"C:/Users/HP/legal-bert-small/model.safetensors",
        description="Path to the GGUF model file"
    )

    @classmethod
    def load(cls) -> "EnvConfig":
        """Load configuration with environment variable override."""
        return cls(
            model_path=os.getenv("MODEL_PATH", "C:/Users/HP/llama.cpp/models/Saul-7B-Instruct-v1.Q4_K_M.gguf")
            #model_path=os.getenv("MODEL_PATH", "C:/Users/HP/legal-bert-small/model.safetensors")
        )

env = EnvConfig.load()

def get_model() -> "Llama | None":
    try:
        model = Llama(
            model_path=env.model_path,
            n_ctx=2048,
            temperature=0.3,
            max_tokens=150,
            n_threads=8,
            n_gpu_layers=0,      # <-- Utiliser 100 couches sur GPU
            # Optionnel : 
            # use_mmap=True,
            # use_mlock=True,
        )
        print("✅ Model loaded successfully with GPU support.")
        return model
    except FileNotFoundError:
        print(f"❌ Model file not found at: {env.model_path}")
    except Exception as e:
        print(f"❌ Error loading model: {e}")
    return None

from transformers import BartTokenizer, BartForConditionalGeneration
import torch

_model, _tokenizer, _device = None, None, None

def get_model_summarizer():
    global _model, _tokenizer, _device
    if _model is None:
        _tokenizer = BartTokenizer.from_pretrained("whyredfire/legal-bart-summarizer")
        _model = BartForConditionalGeneration.from_pretrained("whyredfire/legal-bart-summarizer")
        _device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        _model.to(_device)
    return _tokenizer, _model, _device




# def get_model() -> "Llama | None":
#     try:
#         model = Llama(
#             model_path=env.model_path,
#             n_ctx=2048,
#             temperature = 0.3,
#             max_tokens=150, 
#             n_threads=8,
#             stop=None

#         )
#         print("✅ Model loaded successfully.")
#         return model
#     except FileNotFoundError:
#         print(f"❌ Model file not found at: {env.model_path}")
#     except Exception as e:
#         print(f"❌ Error loading model: {e}")
#     return None

# import os
# from pydantic import BaseModel, Field
# from llama_cpp import Llama
# from typing import Union, Optional
# import torch
# from transformers import AutoModelForCausalLM, AutoTokenizer

# class EnvConfig(BaseModel):
#     # Existing GGUF config
#     model_path: str = Field(
#         "C:/Users/HP/llama.cpp/models/Saul-7B-Instruct-v1.Q4_K_M.gguf",
#         description="Path to the GGUF model file"
#     )
    
#     # New CUDA config
#     use_cuda: bool = Field(
#         default=torch.cuda.is_available(),
#         description="Whether to use CUDA acceleration when available"
#     )
#     hf_model_name: str = Field(
#         default="meta-llama/Llama-2-7b-chat-hf",
#         description="HuggingFace model name for CUDA acceleration"
#     )

#     @classmethod
#     def load(cls) -> "EnvConfig":
#         """Load configuration with environment variable override."""
#         return cls(
#             model_path=os.getenv("MODEL_PATH", "C:/Users/HP/llama.cpp/models/Saul-7B-Instruct-v1.Q4_K_M.gguf"),
#             use_cuda=os.getenv("USE_CUDA", str(torch.cuda.is_available())).lower() == "true",
#             hf_model_name=os.getenv("HF_MODEL", "meta-llama/Llama-2-7b-chat-hf")
#         )

# env = EnvConfig.load()

# def get_model() -> Union[Llama, AutoModelForCausalLM]:
#     """
#     Returns either:
#     - CUDA-accelerated HuggingFace model (if use_cuda=True)
#     - GGUF quantized model (fallback)
#     """
#     try:
#         if env.use_cuda and torch.cuda.is_available():
#             print("🚀 Initializing CUDA-accelerated model...")
#             tokenizer = AutoTokenizer.from_pretrained(env.hf_model_name)
#             model = AutoModelForCausalLM.from_pretrained(
#                 env.hf_model_name,
#                 torch_dtype=torch.float16,
#                 device_map="auto"
#             ).eval()
#             print(f"✅ Loaded {env.hf_model_name} on CUDA")
#             return model
            
#         print("⚡ Initializing GGUF quantized model...")
#         return Llama(
#             model_path=env.model_path,
#             n_ctx=2048,
#             temperature=0.3,
#             max_tokens=150,
#             n_threads=8,
#             stop=None
#         )
        
#     except Exception as e:
#         print(f"❌ Model loading failed: {str(e)[:200]}")
#         raise

