def hello_global_plugin(name: str):
    return f'Hello {name}! I am a global plugin!'

def hello_nested_global_plugin():
    return hello_global_plugin('NESTED GLOBAL')
