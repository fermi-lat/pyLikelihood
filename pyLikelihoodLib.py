#$Id$
def generate(env, **kw):
    if not kw.get('depsOnly',0):
        env.Tool('addLibrary', library = ['_pyLikelihood'])
    env.Tool('LikelihoodLib')

def exists(env):
    return 1
