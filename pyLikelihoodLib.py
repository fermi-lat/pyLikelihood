def generate(env, **kw):
    env.Tool('addLibrary', library = ['_pyLikelihood'])
    env.Tool('LikelihoodLib')

def exists(env):
    return 1
