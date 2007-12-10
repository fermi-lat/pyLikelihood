def generate(env, **kw):
    env.Tool('addLibrary', library = ['pyLikelihood'], package = 'pyLikelihood')
    env.Tool('LikelihoodLib')

def exists(env):
    return 1
