import os

import torch
from diffusers import __version__
from huggingface_hub import constants, hf_hub_download
from safetensors.torch import load_file


class NunchakuModelLoaderMixin:
    @classmethod
    def _build_model(cls, pretrained_model_name_or_path: str | os.PathLike, **kwargs):
        subfolder = kwargs.get("subfolder", None)
        if os.path.exists(pretrained_model_name_or_path):
            dirname = (
                pretrained_model_name_or_path
                if subfolder is None
                else os.path.join(pretrained_model_name_or_path, subfolder)
            )
            unquantized_part_path = os.path.join(dirname, "unquantized_layers.safetensors")
            transformer_block_path = os.path.join(dirname, "transformer_blocks.safetensors")
        else:
            download_kwargs = {
                "subfolder": subfolder,
                "repo_type": "model",
                "revision": kwargs.get("revision", None),
                "cache_dir": kwargs.get("cache_dir", None),
                "local_dir": kwargs.get("local_dir", None),
                "user_agent": kwargs.get("user_agent", None),
                "force_download": kwargs.get("force_download", False),
                "proxies": kwargs.get("proxies", None),
                "etag_timeout": kwargs.get("etag_timeout", constants.DEFAULT_ETAG_TIMEOUT),
                "token": kwargs.get("token", None),
                "local_files_only": kwargs.get("local_files_only", None),
                "headers": kwargs.get("headers", None),
                "endpoint": kwargs.get("endpoint", None),
                "resume_download": kwargs.get("resume_download", None),
                "force_filename": kwargs.get("force_filename", None),
                "local_dir_use_symlinks": kwargs.get("local_dir_use_symlinks", "auto"),
            }
            unquantized_part_path = hf_hub_download(
                repo_id=pretrained_model_name_or_path, filename="unquantized_layers.safetensors", **download_kwargs
            )
            transformer_block_path = hf_hub_download(
                repo_id=pretrained_model_name_or_path, filename="transformer_blocks.safetensors", **download_kwargs
            )

        config, _, _ = cls.load_config(
            pretrained_model_name_or_path,
            subfolder=subfolder,
            cache_dir=kwargs.get("cache_dir", None),
            return_unused_kwargs=True,
            return_commit_hash=True,
            force_download=kwargs.get("force_download", False),
            proxies=kwargs.get("proxies", None),
            local_files_only=kwargs.get("local_files_only", None),
            token=kwargs.get("token", None),
            revision=kwargs.get("revision", None),
            user_agent={"diffusers": __version__, "file_type": "model", "framework": "pytorch"},
            **kwargs,
        )

        transformer = cls.from_config(config).to(kwargs.get("torch_dtype", torch.bfloat16))
        state_dict = load_file(unquantized_part_path)
        transformer.load_state_dict(state_dict, strict=False)

        return transformer, transformer_block_path
