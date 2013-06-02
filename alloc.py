
# Nicholas Prado, register allocator for mips assembly #

# python 3 #
'''
 - instructions not included -
bgezal bltzal b j jal jr noop negu rem remu rol ror bczf bczt jalr abs.d add.d bc1f bc1t c.eq.d c.le.d c.lt.d cvt.d.w cvt.s.d div.d l.d l.s mul.d sub.d break lwcz mtcz mthi mtlo sd sh

I've been away for a while and am transitioning to py3 so all these gotchas are in my sinning way.
'''
class Alloc :

	def __init__(self) :
		self.instr_arity = {
			# nor $t7, $a0, $lo
			"add" : 3, "addu" : 3, "and" : 3,
			"srav" : 3, "srlv" : 3, "sub" : 3,
			"subu" : 3, "xor" : 3, "mul" : 3,
			"mulo" : 3, "mulou" : 3, "srl" : 3,
			"seq" : 3, "sge" : 3, "sgeu" : 3,
			"sgt" : 3, "sgtu" : 3, "sle" : 3,
			"sleu" : 3, "sltu" : 3, "sne" : 3,
			"nor" : 3, "or" : 3, "sllv" : 3,
			"slt" : 3, "sltu" : 3, "addi" : 2,
			# lb $t, offset($s)
			"addiu" : 2, "andi" : 2, "beq" : 2,
			"bne" : 2, "div" : 2, "divu" : 2,
			"lb" : 2, "lw" : 2, "mult" : 2,
			"multu" : 2, "neg" : 2, "not" : 2,
			"ori" : 2, "sb" : 2, "sll" : 2,
			"slti" : 2, "sltiu" : 2, "sra" : 2,
			"srl" : 2, "sw" : 2, "xori" : 2,
			"bge" : 2, "bgeu" : 2, "bgt" : 2,
			"bgtu" : 2, "ble" : 2, "bleu" : 2,
			"blt" : 2, "bltu" : 2, "sltiu" : 2,
			"lbu" : 2, "lh" : 2, "move" : 2,
			# beqz $s0, further
			"beqz" : 1, "bgez" : 1, "bgtz" : 1,
			"blez" : 1, "bltz" : 1, "lui" : 1,
			"mfhi" : 1, "mflo" : 1, "la" : 1,
			"li" : 1
			}
		self.reserved = {
			"arg0" : "$a0",
			"arg1" : "$a1",
			"arg2" : "$a2",
			"arg3" : "$a3",
			"ra" : "$ra",
			"_0" : "$0",
			"out1" : "$v0",
			"out2" : "$v1",
			}
		self.tr_left = 9
		self.sr_left = 7
		self.sp_next = 4 # stack decrements down
		self.used = []
		self.op = 0

	def show( self ) :
		'so my test doesnt become half test, half debugger'
		inp = "add pivot, least, pivot"
		got = self.trans( inp )
		print( "got -{0}-".format( got ) ) # ugh

	def should_trans( self ) :
		inp = "add pivot, least, pivot" # simplest first
		expect = "add $t0, $t1, $t0 # pivot, least, pivot\n"
				# put some context in the comment later, x = y, z
		got = self.trans( inp )
		assert expect == got, "\n\toutput didn't match: " + got

	def auto( self, file ) :
		raw = ""
		try :
			asm_file = open( file )
			for line in asm_file : # more advanced means changing this or processing later
				if line == "\n" :
					continue
				raw = line.rstrip( '\n' )
				print( self.trans( raw ) )
			asm_file.close()
		except IOError :
			print ( "File Error: Perhaps an invalid name?" )

	 # line is split on spaces
	def trans( self, line ) : # or multiple lines
		pieces = line.split( ' ' )
		if self.noop_line( pieces[self.op] ) :
			return line # better to join them together from pieces?
		elif pieces[self.op] in self.instr_arity :
			return self.trans_line( pieces )
		else :
			return line + " #<- no matching parse rule"

	# comment, tag:, 0 arity, blank already handled
	def noop_line( self, symb ) :
		first_char = symb[0] # refactor control flow later
		last_char = symb[-1]
		if first_char == "#" : # comment
			return True
		elif last_char == ":" : # tag, to avoid below greedy test
			return True
		elif first_char == "j" : # jumps
			return True
		else :
			return False

	def trans_line( self, piece ) :
		# print(piece) # woo, debugging
		replace = self.instr_arity[ piece[self.op] ]
		out = piece[self.op] + " "
		done = []
		which = 1
		while which <= replace :
			assigned = self.assign( piece[ which ] )
			out = out + assigned + " "
			done.append( piece[which] )
			which += 1
		if out[-2] == ',' :
			out = out[0:-2] + " " # omit that comma
		out = out + "# "
		for sym in done :
			out = out + sym + " "
		if len(piece) > replace + 1 : # has comment, so put rest
			which += 2 # skip the #, -assumes hash always has space-
			while which < len(piece) : # -1 ?
				out = out + piece[which] + " "
		#out[-1] = '\n' # replace extraneous space like a real man.
		out = out[0:-1] + '\n'
		return out

	def assign( self, symbol ) :
		if symbol in self.reserved :
			return self.reserved[ symbol ]
		# ugh, hacking in similarity to avoid functionality I'll put in later.
		if symbol[-1] != ',' :
			symbol = symbol + ","
		# that's never become a problem later, hahaha.
		if self.already_seen( symbol ) :
			return self.prior_reservation( symbol )
		elif self.t_reg_open() :
			return self.temp_r_chosen( symbol )
		elif self.s_reg_open() :
			return self.sav_r_chosen( symbol )
		else :
			return put_in_stack( symbol )

	def t_reg_open( self ) :
		return self.tr_left >= 0
	def s_reg_open( self ) :
		return self.sr_left >= 0

	def temp_r_chosen( self, symbol ) :
		which_r = 9 - self.tr_left
		self.tr_left -= 1
		reg_name = "$t" + str( which_r ) + ","
		self.used.append( (symbol, reg_name) ) # putting in a tuple
		return reg_name

	def sav_r_chosen( self, symbol ) :
		which_r = 7 - self.sr_left
		self.sr_left -= 1
		reg_name = "$t" + str( which_r ) + ","
		self.used.append( (symbol, reg_name) )
		return reg_name

	def put_in_stack( self, symbol ) :
		self.sp_next -= 4
		place = "$sp-" + str( self.sp_next ) + ","
		self.used.append( (symbol, place) )
		return place

	def already_seen( self, symbol ) :
		sym_spot = 0
		for tup in self.used :
			if tup[ sym_spot ] == symbol :
				return True
		return False

	def prior_reservation( self, name ) :
		for tup in self.used :
			if tup[ 0 ] == name :
				return tup[ 1 ]







bla = Alloc()
bla.show()
bla.should_trans()
# auto( "sample.asm" )

