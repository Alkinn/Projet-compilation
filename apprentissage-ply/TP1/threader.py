import AST
from AST import addToClass

@addToClass(AST.Node)
def thread(self, lastNode):
	for c in self.children:
		lastNode = c.thread(lastNode)
	lastNode.addNext(self)
	return self

@addToClass(AST.WhileNode)
def thread(self, lastNode):
	lastNode = self.children[0].thread(lastNode)
	lastNode.addNext(self)
	lastNode = self
	lastNode = self.children[1].thread(lastNode)
	return self

def thread(tree):
	entry = AST.EntryNode()
	tree.thread(entry)
	return entry

if __name__ == "__main__":
	from parser1 import parse
	import sys, os
	prog = file(sys.argv[1]).read()
	ast = parse(prog)
	entry = thread(ast)

	graph = ast.makegraphicaltree()
	entry.threadTree(graph)

	name = os.path.splitext(sys.argv[1])[0]+'-ast-threaded.pdf'
	graph.write_pdf(name)
	print "wrote threaded ast to", name