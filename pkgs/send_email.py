# -*- coding: utf-8 -*-

import sys
import yagmail

args = sys.argv[1:]
to = args[args.index('-t') + 1]
subject = eval(args[args.index('-s') + 1]).decode('utf-8')
contents = eval(args[args.index('-c') + 1]).decode('utf-8')
yagmail.SMTP('yishaiphone@gmail.com', 'yP1q2w3e4r!').send(to=to,
                                                          subject=subject,
                                                          contents=contents)
