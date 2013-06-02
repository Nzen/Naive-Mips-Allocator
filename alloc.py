
# Nicholas Prado, register allocator for mips assembly #

# python 3 #
'''
 - instructions not included -
bgezal bltzal b j jal jr noop negu rem remu rol ror bczf bczt jalr abs.d add.d bc1f bc1t c.eq.d c.le.d c.lt.d cvt.d.w cvt.s.d div.d l.d l.s mul.d sub.d break lwcz mtcz mthi mtlo sd sh
'''
instr_arity = {
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
reserved = {
	"_arg0" : "$a0",
	"_arg1" : "$a1",
	"_arg2" : "$a2",
	"_arg3" : "$a3",
	"ra" : "$ra",
	"_0" : "$0",
	"_out1" : "$v0",
	"_out2" : "$v1",
	}
tr_left = 9
sr_left = 7
sp_next = 4 # stack decrements down
used = []
#op, tar, sr1, sr2 = range( 0, 3 ) # woo, enums
op = 0

def should_trans() :
	in = "add _pivot, _least, _pivot" # simplest first
	expect = "add $t0, $t1, $t0 # pivot, least, pivot\n"
			# put some context in the comment later, x = y, z
	assert expect == trans( in ), "output didn't match expected"

def auto( file ) :
	raw = ""
	try :
	asm_file = open( file )
	for line in asm_file : # more advanced means changing this or processing later
		if line == "\n" :
			continue
		raw = line.rstrip( '\n' )
		print( trans( raw ) )
	asm_file.close()
	except IOError :
		print ( "File Error: Perhaps an invalid name?" )

 # line is split on spaces
def trans( line ) : # or multiple lines
	pieces = line.split( ' ' )
	if noop_line( pieces[op] ) :
		return line # better to join them together from pieces?
	elif line[op] in instr_arity :
		return trans_line( pieces )
	else
		return line + " #<- no matching parse rule"

# comment, tag:, 0 arity, blank already handled
def noop_line( symb ) :
	first_char = symb[0] # refactor control flow later
	last_char = symb[-1]
	if first_char == "#" : # comment
		return true
	elif last_char == ":" # tag, to avoid below greedy test
		return true
	elif first_char == "j" # jumps
		return true
	else
		return false

def trans_line( piece ) :
	replace = instr_arity[ piece[op] ]
	out = piece[op] + " "
	done = []
	which = 1
	# not unrolling loop for now
	while which <= replace :
		assigned = assign( piece[ which ] )
		out = out + assigned + " "
		done.append( piece[which] )
		which += 1
	out = out + "# "
	for sym in done :
		out = out + sym + " "
	if len(piece) > replace + 1 : # has comment, so put rest
		which += 2 # skip the #, -assumes hash always has space-
		while which < len(piece) # -1 ?
			out = out + piece[which] + " "
	out[-1] = '\n' # replace extraneous space

def assign( symbol ) :
	if symbol in reserved :
		return reserved[ symbol ]
	elif already_seen( symbol ) :
		return prior_reservation( symbol )
	elif t_reg_open() :
		return temp_r_chosen( symbol )
	elif s_reg_open() :
		return sav_r_chosen( symbol )
	else
		return put_in_stack( symbol )

def t_reg_open() :
	return tr_left >= 0
def s_reg_open() :
	return sr_left >= 0

def temp_r_chosen( symbol ) :
	which_r = 9 - tr_left
	tr_left -= 1
	reg_name = "$t" + str( which_r ) + ","
	used.append( (symbol, reg_name) ) # putting in a tuple
	return reg_name

def sav_r_chosen( symbol ) :
	which_r = 7 - sr_left
	sr_left -= 1
	reg_name = "$t" + str( which_r ) + ","
	used.append( (symbol, reg_name) )
	return reg_name

def put_in_stack( symbol ) :
	sp_next -= 4
	place = "$sp-" + str( sp_next ) + ","
	used.append( (symbol, place) )
	return place
	













