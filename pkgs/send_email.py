# -*- coding: utf-8 -*-

import sys
import yagmail

args = sys.argv[1:]
to = args[args.index('-t') + 1]
subject = args[args.index('-s') + 1].decode('ascii')
contents = args[args.index('-c') + 1].decode('ascii')
yagmail.SMTP('yishaiphone@gmail.com', 'yP1q2w3e4r!').send(to=to,
                                                          subject=subject,
                                                          contents=contents)
