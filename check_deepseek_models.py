import sys
sys.path.insert(0, '/home/xiaobai/hermes-agent')
from hermes_cli.models import _PROVIDER_MODELS
if 'deepseek' in _PROVIDER_MODELS:
    print("DeepSeek models:", _PROVIDER_MODELS['deepseek'])
else:
    print("No 'deepseek' key in _PROVIDER_MODELS")
    print("Available providers:", list(_PROVIDER_MODELS.keys()))
