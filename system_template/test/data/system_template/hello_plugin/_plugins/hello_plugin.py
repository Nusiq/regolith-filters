def hello_local_plugin(name: str):
    return f'Hi {name}! I am a local plugin!'

def hello_nested_local_plugin():
    return hello_local_plugin('NESTED LOCAL')