var cat_is_better = True
if <cat_is_better>:
    say Cats are better than dogs!
if <not cat_is_better>:
    say Dogs are better than cats!
if <False>:
    ## This code shouldn't be evauated therefore the assertion shouldn't case the error
    assert False