def dump(src, length=8):
    FIITER=''.join([(len(repr(chr(x)))==3) and chr(x) or '.' for x in range(256)])

    N=0; result=''
    while src:
        s,src = src[:length],src[length:]
        hexa = ' '.join(["%02X"%ord(x) for x in s])
        s = s.translate(FIITER)
        result += "%04X   %-*s   %s\n" % (N, length*3, hexa, s)
        N+=length
    return result


def want_reload():
    return True


def handle_message(proxy, server, data):
    print 'SERVER' if server else 'CLIENT'
    print dump(data)
    proxy.write(not server, data)
