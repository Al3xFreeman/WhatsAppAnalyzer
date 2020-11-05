import ply.lex as lex

tokens = (
    'DATE',
    'HOUR',
    'SENDER_MSG'
)

t_DATE = r'([0-9]+)\/([0-9]+)\/([0-9]+)'#r'(\n)?([0-9]+)\/([0-9]+)\/([0-9]+)\, ([0-9]+)\:([0-9]+) [AP]M '
t_HOUR = r'\, ([0-9]+)\:([0-9]+) [AP]M '
t_SENDER_MSG = r'\- ([\w ]+)\:([\w\d \n]+)'

# Error handling rule
def t_error(t):
     print("Illegal character '%s'" % t.value[0])
     t.lexer.skip(1)
 
# Build the lexer
lexer = lex.lex()
 


