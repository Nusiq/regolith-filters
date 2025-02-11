UNPACK:SUBFUNCTION

definefunction <func_a>:
    summon nusiq:namespaced_entity ~ ~ ~
    function <subfunc_a>:
        say subfunc_a
    function <subfunc_b>:
        say subfunc_b
    say func_a

definefunction <func_b>:
    functiontree <functree_a><@s scrA 0..4>:
        functiontree <functree_b><@s scrB 0..4>:
            say A:`eval:scrA` B:`eval:scrB`
