say TEXTURES: `eval:','.join(textures)`

var textures = [p.with_suffix('').as_posix() for p in Path("pathlib_test").glob("*.png")]
say TEXTURES 2: `eval:','.join(textures)`
