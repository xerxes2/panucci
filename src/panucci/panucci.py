#!/usr/bin/env python
# A resuming media player for Podcasts and Audiobooks
# Copyright (c) 2008-05-26 Thomas Perl <thpinfo.com>
#
# http://thpinfo.com/2008/panucci/
#
# based on http://pygstdocs.berlios.de/pygst-tutorial/seeking.html

import sys, os, thread, time#, traceback
import pygtk, gtk, gobject
import pygst
pygst.require("0.10")
import gst
import cPickle as pickle
import webbrowser
import dbus, dbus.service, dbus.mainloop, dbus.glib


try:
    import hildon
    has_hildon = True
except:
    has_hildon = False

images = {
        'bookmark-new.png': """
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""".decode('base64'),
    'media-playback-pause.png': """
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAAAZhJREFU
WIXtlt2K00AYhp9JJiFfUsgmbQj13CtSXPDiBPFA/LshL8ATaZfqqrA283qwtVBs2dk5Ne/RMO/D
5GGGDwJz5sz53+MimCdAc6H7AXyJZM7GRwjUz6+ffT5XfHz36ekjmDSBtm0F8P7tB+5+3wFQ+ILr
ly9o21a73S6KuZQsVkASm81Xbm42/3QxTLLA1dXV8fBp2rOf9kzTdNLFMMkCq9UqAASF454O679d
DJMssFwudTgRl2U4HJJOuhgmWWCxWAggSORZfviOTroYJllgGAaVZQkS32+/8fPXLUGBsiwZhkGx
zKU8OIZ1XYfKKoQoigJwIKisoq7rEMsk38B6vZaZAY7Cl3h/72xmxxGLYZJvoCxLmRkO8N4f39bM
jiMWwyQL9H0vqypwDu89IRwOryr6vlcskyzQdV24v17IXAZZQAgzo+u6EMskC4zjKDNDEmY1kg5r
YxxHxTLJAk3TyKzi9ZtXJ/tmFU3TKJa5lAf/B7bbbZvneX6um6Zp6vt+F8MkCwBIOjuuzrnwGGbO
nDnn8geBSAonMN700wAAAABJRU5ErkJggg==
""".decode('base64'),
    'media-playback-start.png': """
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAAA7tJREFU
WIXtlk9oXEUcx7+/mffeJpjdTbpZs2Z3m83WHDTBQ9hirMaeAm0S4yU16aEQiiAFiwcRW6kkoodq
NLkVpC32FJEcLFoQqWCKKApeWihCqMpmS5Ju9m3cNMn7tzPjYTeKEDbbmMaD+cKc5r35fd53fvOd
B+xpT/+x+BbzzQAaAHjlsesAkaN9PR8ZumYuLZkWAAeA2E2AUDLZeqG9veOl5uhjrcv5P2bX19cF
ABuA2hWAA48nT09NfcZbWhJPLC7On4g0N2FhfnFOCCFRcuThAwwOHkNDqJ4GBgZ0w9C7pBLHAv66
9Pz8wgqAIgD3oQIMDQ3DdR0oJdHe0cGPHDnqX8rl+kP76p9TSsya5rKLbfZH1QCeV/pIKSU4Z+ju
PsxTqYOxTCYz3BxrfjS3lLtj2zbKIHJHAAKBQCgWj/4DYENSCvgDfvT19fP98fhTOTN7ItLUZOXz
y3d9Ph8cx7H/NUAymQwFg/7TQ8PHURRFMCIQsb8HCFIKxKIx6n9hwABUN0G8WBcM/lpbU7ve2Ngo
TNOs2B9UabKnp6eNmJy9evULWLYFooqPgzOO+6urGP/gvDeXznx/31p7m0mWdl13aWZmZlNHWKUF
o9FoiZIYOOfgjINzDsZKDiilIKWAV/RgOzZWVguQqojR0Xf00bGxw8G6uu8C9XWvJRKJ+MjISM0D
A4TDYQCAUhKWbcF2LNi2Bcd14HkOhChCSAkoBUYEjWvw+WrAGcfC/IK0LAucWDocDmNtbW3TKNcq
AcRiMdz+5RaIGDSugbGNHiAQqLSBClDlUNQ1A5nMHCYmx13HcT999tAzE37/voV8Pm9OT09vejIq
AkSjURi6ASL6awsYYyDGwIiw0UKccxQKBUxOTnh35zI/JxL7z7a1PflbMBjM9vb2VkzLLR3QdR0E
gBEDMQJjDKzcC5xzWOsWrl370rt+/etsuDF85tSpV38QQuS6urpWKq1dvQOGDgVAKgmSBAkJxhik
kLh186a8/MlFu76+4cOzZ85N1dbW5iORiElEVQdRVQ4opSBEsfSCpiN77x4uXvrYVQqfv3zylfHO
zs4sgCwRPfDlVBEAAAzDgFISmqZDCoUrVy576fTvtw+mnn5zcHDoDoAcEVVl97YAdF0H5xp++vFG
8duZb8x4vOXc++cnbgAolItXbff2AAwd7743Zvsf8V944/W3LoVCoVVs0+5tAbS2to4d6nr+q1Qq
lQNgElFhJwpvqGK4K6UOoJSWhXLxHf0f3FJKKV0p5dvVonv63+lPeip8lRfpXtkAAAAASUVORK5C
YII=
    """.decode('base64'),
    'media-seek-backward.png': """
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAAA+lJREFU
WIXtlF1MW1UAx//3nHt7b1ukFEpbbTEpbDiUj0IIMBBx2eKWGB8w4UkhPGhMfFAw82FGXYxPPkLn
ky884xITkyUEx3QhwpAhWDqwoVJKb9tZWuhlCoXeDx8GyIIFJosv9pfcl5vfOed37scBcuTI8X+H
/stxLAArAAsABkD6CftZYQCY88x5lW0vt371ysXzGoDSk/jkMRbXA3i2vr729baWlptdXV2dO/ez
PcV9fut33d3dbx7hZ4UCsLlcrpcuXrpw64MPe/6UpJSmaZr26muXtgGUncRnj1jcxPO8vfFsw1vF
lqJ3r1z5iHfX1NH01iZUVX0SftYAAUCx213V+ozD8UV7e7ulq7NbUDUF639IADToBcNJ/KwBBECR
w+Eoq6p+/hOXy3Xu6tXP9EVFFmxtpaEoMgghYMDsH8M4HA73Y/hZAziLxeKqqal6o8BsutzT08s3
n32RZuQMNtObADQwzO43qwEAKEuZc+fbOosKzZffe7+Xb25qoZvpDaylVqFBBTQGmqYBDJBnfAq8
TgdBELR0On0wwGQy5TU3N3QKeuHj/v4vYbPakVhbQSaTASUEDEPAMAwYBsDOjgQdz+qLhU/7+q49
9FfjyMjy3z551DcYDQzP89gfsPdLVFZWKsnk2uLTdltq/M5Yg81mI2WuMkIIhaqqYFl25+LAshx0
nA43R4blbUX+fOLOeIP1GP7w8JAiilGPJEmpAwGxWEyNx+OSTifMbm9tfitGwk6fz+t0V9dyBSYz
NGighICjDyemhOL72yPKxNjdt2V562sxEnH67nmd7mp3Vv+H27fU4GLoWjKZPBiw+3JjsdhGefmZ
RHAxNMKx3Ix3drpRlmW+/NRzLKXs3sSEEPw4NqqK4Wh/JBILSKn1EUqYGd89b6MsZ/jT/+SPj6rR
yH2PKIpZAwAAgUBAEUXxgdNZEkqsxK5n5K3M9C8/1zmdJaSwsJAoqgJKKH6anFDDy2L/1NRUUhTF
BwaDMbSa/P26rCoZ7+x0ndNRQsz7/MnJCXU5JPYHg0Hp0IBd/H7/dlVV7fpSMDzDUnIjGhNLI5Gw
rfz0GY7jOExPT6pLS2HPwsKCBADhcHi7trZ+PbQUnqFEdyN2f7k0Eo3Yyk/t+DN31V/nFzzHDgCA
ubk5LRAIbFRUvLCyHBKHDHre7w/MN6mKyq4k43wsGu/z+Xypg37FSigkDukFnX/ht/kmRVbYRCLO
x+PJR/yjjuI9BgYG0gBi+fn531it1nGO9/YajcZ39Hq9cpRfkJDGWZbrNeYd9LMfUYcwODhIR0dH
CxVFESilksfjWT/M7+jooHa7/dh+jhw5/lP+Akl39GFkFh9JAAAAAElFTkSuQmCC
    """.decode('base64'),
    'media-seek-forward.png': """
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAABGxJREFU
WIXtlFtsFFUYx/9nLju7O7OzszPusssud+pLgbWYYIxJC0EKiRfAWB+aUoUXnqwl+KYRIhESuZPw
KuKDD5qCDybVxAR4QYRAa4wGlHaLKVja7uxuu9u5z/Fhaa1l28Kbif0nk3zJ+Z3JL9/5zgEWspCF
/N/DTqtVAIsACAAsAP48e5+Wn1cg3bx1c9/iTJop6IUB27bdRz+eLU/LzyugrVq98t09u/c8N14u
tUhyZHDowZAOwAbg1tirrlq9suOdt3c3lCtjLVFFGSzoBd113dn4uQVkWVYzS9IdRz89zm9pbpbv
5XLbYmo0y3GBO6Zp2rZtmwDoJJ9IJGLJ1KKOY0dPcFuat8q5/r5tshzJhkLhOwzDWOVy2ZrOzyuQ
SCRi8bjWsautHZT6ePWV1/i6Z+uW3/n9duszcc0Xw9KALMuerusWAKRSKTWmKjP41ct/u/1ra1SR
fTWm3ZNl2c3n8/YTCSxbtiwWiYjv7Wprx3hlHI5rI5NZyrS8+VbANCc2jOYf7gwFhb5YTCtpmmbJ
siyHQkJt3jBeGBq+v1MMh/tTqXRJlmVrZGTEqyVAJovGxsYVwRDf//13P6A4VgABAQjAsxwEIYSH
w0M4cOAjc+jhX92m4xxiPKYI4j3GcyyH4AzeAw4F2eCf2Wy2cPDgwX/dlqkONDQ0KCC0s7W1DYWS
Ds/z4Ho+XNeBaRmQpAh2bH+DW5zO1P3yc28bYUmREGxubW2DZVsgDAFDGACA6zqQpAi2v76DS6fT
dT03b7b5vm9UKhODqqqWBwYGpiSYyUJRFEiSCADgWB4sy4FjGRDCgFKgPFFGabyITU2buBMnTkdC
QeGwKFZ527arn2PBtEwYpoHiWAGl8SI2Nm3iTp48EwkI3GHft1rWrl0bnt4BbrLQNI0WilUxQQiC
kOrpUOrD930EeAFBQcC1n350z39xzojK0cOO6xyZn7/qfn7+nBFTYp9Eo9qX4XB4oqZAPB6ntlNd
CwYEgBBQvyrE8wHoeh6nTh839LzerSbih+SgrA/eHzgyJ3/qmKHrencilfpYjaj3Ojs7S4QQWlMg
EolQ8dERsBwH3/fB8jyoT9Hd/a15/ca1Bwxh92fXrb9qGEaB5/lkoTQyO3/92gOeZ/dn1z1/1TCM
wt69e519+/ZhZqYEotEo1YtVAc/zwHM8+nN97sVvuizf946tqW/4zDTNfHt7ewUAurq66OQM/MPf
dS9c7LIo9Y+uWdNwbjo/W6YEVFXFyGh1PmzbxoWLXxuj+ZHLyUTiw0xmRf+VK1fGpl8hRVGoNG0I
uy58ZeTzo5eXpBd/kEwuzc3k5xVQFIWKkohbPTeM3t5beS4QeH99dsMlRVGK9fX1j71mmqZBlMK4
2XPd6O25lRcCof0vvdh0SRCEUi3+SQR8URTRn/vjTFPjy2crlYqezWZnbd8kn8vdPbOxactZSZL0
ZDI5Z7trZeolHB4eliilYiAQsBRFGSOEzNk+SqlUqVREx3GeiF/IQhbyn83fWcMofSJnzd4AAAAA
SUVORK5CYII=
    """.decode('base64'),
    'media-skip-backward.png': """
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAABItJREFU
WIXtk1tsVEUYx/9z5pwzs2fO7p6z3UshpUhMFLX2hiZViCSUiG/aIvpAxBqJaKKVYmLVkHYbEkiL
QRB9RS6VAIUWeMCCmPBStWVVYgPGupa20EBsUyhdurvs5fiw2+2FsogPvth/cnKSmV9mfvPNN8Bc
5jKX/3tI+u9Kf2TKnAVgJP1liwzADYADGAVw40F4eULg+VXlf8wkv+/oLAiFQvcSIAAMXdfnL1lS
XM04e+vM6e8eziIwKy9PmcTp9rMZetUL5WOccxYKhWZbzAbAU1paVD5vfu62iorVxpEjhwGA3mPz
Kfz8rZWVlebhw4cAgMozyeGRIbhdnnusAwrAvWjRgkceXbzY/3jBE2V1m/2a0+FE2/HWGIDk/fj6
zX7N4XCite1YDEDyLoEscTLGfGVlT7/p9rjf/ejjT1hJUSmNRMNIJmfu+8/5uwTIzAGAAfCWlBQu
m5c3r/GlFys8r7/2Bk9aCdwKjQKwYOPav+YnBKyJASpPOhFCrLy8vKKCwsfqHlq4sLy+fgt3u92I
RiNIJOKQJAlkujKZyvvrt/Cc7HxKwOFwgNJU/9B0W1BKpeLiJ9faHfZ3NtZsYkufWUZj8RjCkTAA
C4RI09ypTMmKFc+tNV3mh+9v3MSeLVtKw5Fx3Lg5AgtJwCKwLAsggC7sYKoKzrklA4DT6bSELgAA
d2J3AAC6rgtCyAe7Pv8Sud5cDN8YQiwWA5UkECKBEAJCJi+Nq0y2ebl/164v4PPmYnjkL8Ti8Ule
ms5rQiOMMUgAwBiDLlICqqKmAE27LSvypw3+uvHz5zsTLqcLdt0BSmUoigJVVaGqHIxxEEJgGEac
SMTf0FA/fj7QmXAZOVl5oQnLMAxLAgDTNC2RFuCMAwCEEMlrg0PNA/19y/cf2NfeuH1rJBqJwnCY
UBQVMpWhykpGWOjCutj9+4H+vqvLDzTva2/avu1+PDjnqQrYbLaMwESELmAYBixL7v4pcGFD7+XL
VTs+axo4c7Y9whQGVWEAIZBSdYUQAkKIZE9PT3eg68KGP4O9VTt3bh/49uzp2XldwDTNVA9wziH0
1NOIRiNQZAV2XQfnktXW9k0UwKDH4zk1OHA9QClZf/FSd/XLla+y/PyFNB6PgQIQQoemaVYwGIwG
g8FBSZJO9fb2B4gkrb/0W3f16opX2IKpvCagaVrqCjRNy1QgEg1nTsSYPfM8T548Oabrel+g69cd
fQNXV7Ydbzl39Nih8WQimb5TDs55poIdHR1jOTk5fYGuCzuu9F9Z2Xri6LljrUcyvKbZJp+hYRiZ
JnS7vOkS2WCa5rRraWlpSQAYqvJVjXX9+Mu6kpJY+f6v9zQVF5aajDPmcDjIbLzPVzV2/Yef18We
ipc3H/yqqaiwxOSMMa/XS2QAUFU1KXSB5oN7JntA6HZZliOYJXv37o0AuObxvHfi5s3bnUxlNUKI
t202WyIbTyk94fP5OmVFqRF6iicAUFtb6wTgjMfjmRPIsmwBGG1sbBydbdGJrFmzhubn55vhcNhG
KR3dvXv3rQfhs7Fzmctc/pP8Dd1XoHZ87jPMAAAAAElFTkSuQmCC
    """.decode('base64'),
    'media-skip-forward.png': """
iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABHNCSVQICAgIfAhkiAAABIBJREFU
WIXtlVtMHFUcxr+zM8PMzpnuMl1jehHbQIwvNRSVmhRcMMUWk/puatWXFhOjRkMbXkjcJm00sUIl
JUWIBY0hTUmpSRu3JTWmli1U2l3AiqmVgmjZctuLC8yFZY4Ps2u3FFr64ot8yckkZ37zP998539m
gBWtaEX/d5HUdTUAFwANwBSA5EOee1TeA0DNWA8AGIApPl1w+45tNzXdqOkN9jUlEok7AOIpaFED
j8ATRVHWbC164frCGx3nv89zpCEAqNi79x1vSdGFgoL8VwHkAJCWMEAAYO+ePcvhiSRJIqV0+vy5
C0gPgCUAEEcmufv1N6Xm5q/Xe0u8X5SXv9y0YcOGZwE8DoBbzMUbu9+SWlqWz1uWhcnIxD1zjoWQ
0ynis8O1zo8OHNj23PP5HcXere+LopgLe8/vkyQ9Gr9Q9xkwTBOJmTg25xdwra0n6a7XdlWWbX+p
Iz9/UznsmMXF+c3L4h9qgOM4EDhgmDrmk3OoqHhbamr8cuOWLVu+2vFKWd3anLXPIKPZ7vIGkim+
MYNfk7NmEyHkHj5DLH0KmCAIAABNn4WDOADigEkMzGizcLlcOHasUeoMXNp59OjnZZNPRT4RBPtR
Qog9QMAYg6Zr8Kz2oKGhSeoM/Lizru5IWTQWr+d5ngAAz/EpIzzcbjd4AHC5XFAUChsQUkUBxgDG
GKZnp2GYBkq8pXxeXp6yb9+HBxmzX8o0zfv4GW0GWUIWvC+W8rm5eUpl5QdVTqcThACmaQAAKJWR
nZ1tJ+B2uxmltgFRlECI/b1gzIJlWcgSREiiiCs/dSVbWpp1AvKxTOVDy+Gbm4/rHM8dpVR+DyBU
ELJSBhRIkmQnIIoi0gakLBEgBMyyAACCkIVINIIjRw7rY2Pj/qG/Rg6ODo/GSkqLDj2Ir639VB8f
H/cP/TlyaG52Lrlu/bp304bTCaiqaiegqiqjqS3geB7MskB4AYwxfHfurH6lOxAevT22PxTq7zJN
c1KW5SeW4v3+s3p39+Xw2Nid/QMDv3cJghBRVfVp2UlBCAHnsPueKhSyLNsGnE7nv1swPz8PgRcw
NHwr2X66zYhHozXd3cEWTdMmQqFQAgC8Xu8i/GDyVHubEYvFavpCv7TEYrGJQCCQ8Pl8jhs3fmaK
QsEYg2Ea4HkBiqLYPQcAkiRBoTIAYM400f5tmzYavn1x+NaQb2QkPFhcXBzx+XxW+uy43W4oKQNz
polTp09q4fDoxT+Ghn0jI+HBwsLCe3hRXMWobNfXDR1UVkCpDEqpnYAsy4wqFMFQjxYMXY1MTkaq
+kLXf4jH41N+v984c+ZM5tkFpZRRRca1UI8WvNYTmZqMVvX1Lc2rqgqZyiCEwKM+BgBQ7B6wE/B4
PIxSilDv1fr+3l8bIpHIxIkTJxJY4m9IKWWUUvT3B+tv/jbcoOv6krzP52PV1dW6IPDKN63H79ZQ
lFVut9viAYDjuFjgUs+TyWRSi0aj0ba2tvnFFk6L47jY5c6ry+XZ9PT0RG9wYGPmJM/zDMDfD1pn
RSta0X+ifwD5ei3DfRRvPQAAAABJRU5ErkJggg==
    """.decode('base64'),
}

about_name = 'Panucci'
about_text = 'bookmarking audio player'
about_authors = ['Thomas Perl', 'Nick Sapi', 'Matthew Taylor']
about_website = 'http://thpinfo.com/2008/panucci/'
donate_wishlist_url = 'http://www.amazon.de/gp/registry/2PD2MYGHE6857'
donate_device_url = 'http://maemo.gpodder.org/donate.html'


def open_link(d, url, data):
    webbrowser.open_new(url)
        

gtk.about_dialog_set_url_hook(open_link, None)


def image(widget, filename):
    widget.remove(widget.get_child())
    if filename in images:
        pbl = gtk.gdk.PixbufLoader()
        pbl.write(images[filename])
        pbl.close()
        pb = pbl.get_pixbuf()
        image = gtk.image_new_from_pixbuf(pb)
        if os.path.exists('/etc/init.d/maemo-launcher'):
            image.set_padding(20, 20)
        else:
            image.set_padding(5, 5)
        widget.add(image)
        image.show()

class PositionManager(object):
    def __init__(self, filename=None):
        if filename is None:
            filename = os.path.expanduser('~/.rmp-bookmarks')
        self.filename = filename

        try:
            # load the playback positions
            f = open(self.filename, 'rb')
            self.positions = pickle.load(f)
            f.close()
        except:
            # let's start out with a new dict
            self.positions = {}

    def set_position(self, url, position):
        if not url in self.positions:
            self.positions[url] = {}

        self.positions[url]['position'] = position

    def get_position(self, url):
        if url in self.positions and 'position' in self.positions[url]:
            return self.positions[url]['position']
        else:
            return 0

    def set_bookmarks(self, url, bookmarks):
        if not url in self.positions:
            self.positions[url] = {}

        self.positions[url]['bookmarks'] = bookmarks

    def get_bookmarks(self, url):
        if url in self.positions and 'bookmarks' in self.positions[url]:
            return self.positions[url]['bookmarks']
        else:
            return []

    def save(self):
        # save the playback position dict
        f = open(self.filename, 'wb')
        pickle.dump(self.positions, f)
        f.close()

pm = PositionManager()

class BookmarksWindow(gtk.Window):
    def __init__(self, main):
        self.main = main
        gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
        self.set_title('Bookmarks')
        self.set_modal(True)
        self.set_default_size(400, 300)
        self.set_border_width(10)
        self.vbox = gtk.VBox()
        self.vbox.set_spacing(5)
        self.treeview = gtk.TreeView()
        self.treeview.set_headers_visible(True)
        self.model = gtk.ListStore(gobject.TYPE_STRING,
            gobject.TYPE_STRING, gobject.TYPE_UINT64)
        self.treeview.set_model(self.model)

        ncol = gtk.TreeViewColumn('Name')
        ncell = gtk.CellRendererText()
        ncell.set_property('editable', True)
        ncell.connect('edited', self.label_edited)
        ncol.pack_start(ncell)
        ncol.add_attribute(ncell, 'text', 0)

        tcol = gtk.TreeViewColumn('Time')
        tcell = gtk.CellRendererText()
        tcol.pack_start(tcell)
        tcol.add_attribute(tcell, 'text', 1)

        self.treeview.append_column(ncol)
        self.treeview.append_column(tcol)

        sw = gtk.ScrolledWindow()
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        sw.set_shadow_type(gtk.SHADOW_IN)
        sw.add(self.treeview)
        self.vbox.add(sw)
        self.hbox = gtk.HButtonBox()
        self.add_button = gtk.Button(gtk.STOCK_ADD)
        self.add_button.set_use_stock(True)
        self.add_button.connect('clicked', self.add_bookmark)
        self.hbox.pack_start(self.add_button)
        self.remove_button = gtk.Button(gtk.STOCK_REMOVE)
        self.remove_button.set_use_stock(True)
        self.remove_button.connect('clicked', self.remove_bookmark)
        self.hbox.pack_start(self.remove_button)
        self.jump_button = gtk.Button(gtk.STOCK_JUMP_TO)
        self.jump_button.set_use_stock(True)
        self.jump_button.connect('clicked', self.jump_bookmark)
        self.hbox.pack_start(self.jump_button)
        self.close_button = gtk.Button(gtk.STOCK_CLOSE)
        self.close_button.set_use_stock(True)
        self.close_button.connect('clicked', self.close)
        self.hbox.pack_start(self.close_button)
        self.vbox.pack_start(self.hbox, False, True)
        self.add(self.vbox)
        for label, pos in pm.get_bookmarks(self.main.filename):
            self.add_bookmark(label=label, pos=pos)
        self.show_all()

    def close(self, w):
        bookmarks = []
        for row in self.model:
            bookmarks.append((row[0], row[2]))
        pm.set_bookmarks(self.main.filename, bookmarks)
        self.destroy()

    def label_edited(self, cellrenderer, path, new_text):
        self.model.set_value(self.model.get_iter(path), 0, new_text)

    def add_bookmark(self, w=None, label=None, pos=None):
        (text, position) = self.main.get_position(pos)
        if label is None:
            label = text
        self.model.append([label, text, position])
    
    def remove_bookmark(self, w):
        selection = self.treeview.get_selection()
        (model, iter) = selection.get_selected()
        if iter is not None:
            model.remove(iter)

    def jump_bookmark(self, w):
        selection = self.treeview.get_selection()
        (model, iter) = selection.get_selected()
        if iter is not None:
            pos = model.get_value(iter, 2)
            self.main.do_seek(pos)

class GTK_Main(dbus.service.Object):
	
    def save_position(self):
        try:
            (pos, format) = self.player.query_position(self.time_format, None)
            pm.set_position(self.filename, pos)
        except:
            pass

    def get_position(self, pos=None):
        if pos is None:
            try:
                pos = self.player.query_position(self.time_format, None)[0]
            except:
                pos = 0
        text = self.convert_ns(pos)
        return (text, pos)

    def destroy(self, widget):
        self.save_position()
        if has_hildon:
            vol = self.volume.get_level()
        else:
            vol = int(self.volume.get_value()*100)
        pm.set_position( 'volume', vol )
        gtk.main_quit()
    
    def __init__(self, bus_name, filename=None):
        dbus.service.Object.__init__(self, object_path="/player",
            bus_name=bus_name)

        self.filename = filename
        self.make_main_window()
        self.has_coverart = False

        self.want_to_seek = False
        self.player = gst.element_factory_make('playbin', 'player')

        vol = pm.get_position('volume')
        if vol == 0: vol = 20
        if has_hildon:
            self.volume.set_level(vol)
        else:
            self.volume.set_value(vol/100.0)

        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)

        self.time_format = gst.Format(gst.FORMAT_TIME)
        if self.filename is not None:
            gobject.timeout_add(200, self.start_playback)

    def make_main_window(self):
        import pango
        		
        if has_hildon == True:
            self.app = hildon.Program()
            window = hildon.Window()
            self.app.add_window(window)
        else:
            window = gtk.Window(gtk.WINDOW_TOPLEVEL)
                        
        	
        window.set_title('Panucci')
        window.set_default_size(400, -1)
        window.set_border_width(0)
        window.connect("destroy", self.destroy)
        self.main_window = window
        
                
        if has_hildon == True:
            window.set_menu(self.create_menu())
        else:
            menu_vbox = gtk.VBox()
            menu_vbox.set_spacing(0)
            window.add(menu_vbox)
            menu_bar = gtk.MenuBar()
            root_menu = gtk.MenuItem("File")
            root_menu.set_submenu(self.create_menu())
            menu_bar.append(root_menu)
            menu_vbox.pack_start(menu_bar, False, False, 0)
            menu_bar.show()

        main_hbox = gtk.HBox()
        main_hbox.set_spacing(6)
        if has_hildon == True:
            window.add(main_hbox)
        else:
            menu_vbox.pack_end(main_hbox, True, True, 6)

        main_vbox = gtk.VBox()
        main_vbox.set_spacing(6)
        # add a vbox to the main_hbox
        main_hbox.pack_start(main_vbox, True, True)

        # a hbox to hold the cover art and metadata vbox
        metadata_hbox = gtk.HBox()
        metadata_hbox.set_spacing(6)
        main_vbox.pack_start(metadata_hbox, True, False)

        self.cover_art = gtk.Image()
        metadata_hbox.pack_start( self.cover_art, False, False )

        # vbox to hold metadata
        metadata_vbox = gtk.VBox()
        metadata_vbox.set_spacing(8)
        empty_label = gtk.Label()
        metadata_vbox.pack_start(empty_label, True, True)
        self.artist_label = gtk.Label('')
        self.artist_label.set_ellipsize(pango.ELLIPSIZE_END)
        metadata_vbox.pack_start(self.artist_label, False, False)
        self.album_label = gtk.Label('')
        self.album_label.set_ellipsize(pango.ELLIPSIZE_END)
        metadata_vbox.pack_start(self.album_label, False, False)
        self.title_label = gtk.Label('')
        self.title_label.set_ellipsize(pango.ELLIPSIZE_END)
        metadata_vbox.pack_start(self.title_label, False, False)
        empty_label = gtk.Label()
        metadata_vbox.pack_start(empty_label, True, True)
        metadata_hbox.pack_start( metadata_vbox, True, True )

        # make the button box
        buttonbox = gtk.HBox()
        self.rrewind_button = gtk.Button('')
        image(self.rrewind_button, 'media-skip-backward.png')
        self.rrewind_button.connect("clicked", self.rewind_callback)
        buttonbox.add(self.rrewind_button)
        self.rewind_button = gtk.Button('')
        image(self.rewind_button, 'media-seek-backward.png')
        self.rewind_button.connect("clicked", self.rewind_callback)
        buttonbox.add(self.rewind_button)
        self.playing = False
        self.button = gtk.Button('')
        image(self.button, 'media-playback-start.png')
        self.button.connect("clicked", self.start_stop)
        buttonbox.add(self.button)
        self.forward_button = gtk.Button('')
        image(self.forward_button, 'media-seek-forward.png')
        self.forward_button.connect("clicked", self.forward_callback)
        buttonbox.add(self.forward_button)
        self.fforward_button = gtk.Button('')
        image(self.fforward_button, 'media-skip-forward.png')
        self.fforward_button.connect("clicked", self.forward_callback)
        buttonbox.add(self.fforward_button)
        self.bookmarks_button = gtk.Button('')
        image(self.bookmarks_button, 'bookmark-new.png')
        self.bookmarks_button.connect("clicked", self.bookmarks_callback)
        buttonbox.add(self.bookmarks_button)
        self.set_controls_sensitivity(False)

        if has_hildon == False: # hasattr(gtk, 'VolumeButton'):
            self.volume = gtk.VolumeButton()
            self.volume.connect('value-changed', self.volume_changed)
            buttonbox.add(self.volume)
        else:
            #import hildon # this should be unnecessary
            self.volume = hildon.VVolumebar()
            self.volume.connect('level_changed', self.volume_changed2)
            self.volume.connect('mute_toggled', self.mute_toggled)
            window.connect('key-press-event', self.on_key_press)
            main_hbox.pack_start(self.volume, False, True)

        self.progress = gtk.ProgressBar()
        main_vbox.pack_start(self.progress, False, False)
        main_vbox.pack_start(buttonbox, False, False)
        self.progress.set_text("00:00 / 00:00")

        window.show_all()

    def create_menu(self):
        menu = gtk.Menu()
        menu_donate_sub = gtk.Menu()
        
        menu_open = gtk.MenuItem("Open...")
        #haven't quite worked this part out yet - matt
        #menu_open.connect("activate", self.file_open, self.main_window)
        
        menu_about = gtk.MenuItem("About")
        menu_about.connect("activate", self.show_about, self.main_window)

        menu_donate = gtk.MenuItem("Donate")
        
        menu_donate_device = gtk.MenuItem("Device")
        menu_donate_device.connect("activate", lambda w: webbrowser.open_new(donate_device_url))
        
        menu_donate_wishlist = gtk.MenuItem("Amazon Wishlist")
        menu_donate_wishlist.connect("activate", lambda w: webbrowser.open_new(donate_wishlist_url))

        menu_quit = gtk.MenuItem("Quit")
        menu_quit.connect("activate", self.destroy)
        
        menu.append(menu_open)
        menu.append(gtk.SeparatorMenuItem())
        menu.append(menu_about)
        menu_donate_sub.append(menu_donate_device)
        menu_donate_sub.append(menu_donate_wishlist)
        menu_donate.set_submenu(menu_donate_sub)
        menu.append(menu_donate)
        menu.append(gtk.SeparatorMenuItem())
        menu.append(menu_quit)
        return menu

    def show_about(self, w, win):
        dialog = gtk.AboutDialog()
        dialog.set_website(about_website)
        dialog.set_website_label('Homepage')
        dialog.set_name(about_name)
        dialog.set_authors(about_authors)
        dialog.set_comments(about_text)
        dialog.run()
        dialog.destroy()
        
    @dbus.service.method('org.panucci.interface')
    def show_main_window(self):
        # This is supposed to display the window
        # I don't know how to do that :P
        self.main_window.deiconify()

    def set_controls_sensitivity(self, sensitive):
        self.forward_button.set_sensitive(sensitive)
        self.rewind_button.set_sensitive(sensitive)
        self.fforward_button.set_sensitive(sensitive)
        self.rrewind_button.set_sensitive(sensitive)

    def on_key_press(self, widget, event):
        if event.keyval == gtk.keysyms.F7: #plus
            self.volume.set_level( min( 100, self.volume.get_level() + 10 ))
        elif event.keyval == gtk.keysyms.F8: #minus
            self.volume.set_level( max( 0, self.volume.get_level() - 10 ))

    def volume_changed(self, widget, new_value=8.0):
        self.player.set_property('volume', float(new_value))
        return True

    def volume_changed2(self, widget):
        self.player.set_property('volume', float(widget.get_level()/100.*10.))
        return True

    def mute_toggled(self, widget):
        if widget.get_mute():
            self.player.set_property('volume', float(0))
        else:
            self.player.set_property('volume', float(widget.get_level()/100.*10.))

    @dbus.service.method('org.panucci.interface', in_signature='s')
    def play_file(self, filename):
        if self.playing:
            self.start_stop(None)
        self.filename = filename
        self.has_coverart = False
        self.start_playback()

    def start_playback(self):
        self.start_stop(None)
        self.set_controls_sensitivity(True)
        self.title_label.hide()
        self.artist_label.hide()
        self.album_label.hide()
        self.cover_art.hide()
        return False
        
    def start_stop(self, w):
        self.playing = not self.playing
        if self.playing:
            self.want_to_seek = True
            if self.filename is None or not os.path.exists(self.filename):
                if has_hildon:
                    dlg = hildon.FileChooserDialog(self.main_window,
                        gtk.FILE_CHOOSER_ACTION_OPEN)
                else:
                    dlg = gtk.FileChooserDialog('Select podcast or audiobook',
                        None, gtk.FILE_CHOOSER_ACTION_OPEN, ((gtk.STOCK_CANCEL,
                        gtk.RESPONSE_REJECT, gtk.STOCK_MEDIA_PLAY, gtk.RESPONSE_OK)))
                if dlg.run() == gtk.RESPONSE_OK:
                    self.filename = dlg.get_filename()
                    dlg.destroy()
                else:
                    dlg.destroy()
                    return
            self.filename = os.path.abspath(self.filename)
            self.player.set_property('uri', 'file://'+self.filename)
            self.player.set_state(gst.STATE_PLAYING)
            image(self.button, 'media-playback-pause.png')
            self.play_thread_id = thread.start_new_thread(self.play_thread, ())
        else:
            self.want_to_seek = False
            self.save_position()
            self.play_thread_id = None
            self.player.set_state(gst.STATE_NULL)
            image(self.button, 'media-playback-start.png')

    def do_seek(self, seek_ns=None):
        if seek_ns is None:
            seek_ns = pm.get_position(self.filename)
        if seek_ns != 0:
            self.player.seek_simple(self.time_format, gst.SEEK_FLAG_FLUSH, seek_ns)
        self.want_to_seek = False

    def play_thread(self):
        play_thread_id = self.play_thread_id
        gtk.gdk.threads_enter()
        self.progress.set_text("00:00 / 00:00")
        gtk.gdk.threads_leave()

        while play_thread_id == self.play_thread_id:
            try:
                time.sleep(0.2)
                dur_int = self.player.query_duration(self.time_format, None)[0]
                dur_str = self.convert_ns(dur_int)
                gtk.gdk.threads_enter()
                self.progress.set_text("00:00 / " + dur_str)
                self.progress.set_fraction(0)
                gtk.gdk.threads_leave()
                break
            except:
                pass
                
        time.sleep(0.2)
        while play_thread_id == self.play_thread_id:
            pos_int = self.player.query_position(self.time_format, None)[0]
            pos_str = self.convert_ns(pos_int)
            if play_thread_id == self.play_thread_id and pos_str != '00:00':
                gtk.gdk.threads_enter()
                self.progress.set_fraction(float(pos_int)/float(dur_int+1))
                self.progress.set_text('%s / %s' % ( pos_str, 
                    self.convert_ns(dur_int)))
                gtk.gdk.threads_leave()
            time.sleep(1)

            
    def on_message(self, bus, message):
        t = message.type

        if t == gst.MESSAGE_EOS:
            self.play_thread_id = None
            self.player.set_state(gst.STATE_NULL)
            image(self.button, 'media-playback-pause.png')
            self.progress.set_text("00:00 / 00:00")
            pm.set_position(self.filename, 0)

        elif t == gst.MESSAGE_ERROR:
            err, debug = message.parse_error()
            print "Error: %s" % err, debug
            self.play_thread_id = None
            self.player.set_state(gst.STATE_NULL)
            image(self.button, 'media-playback-start.png')
            self.progress.set_text("00:00 / 00:00")

        elif t == gst.MESSAGE_STATE_CHANGED:
            if ( message.src == self.player and
                message.structure['new-state'] == gst.STATE_PLAYING ):

                if self.want_to_seek:
                    self.do_seek()
                else:
                    self.set_controls_sensitivity(True)

        elif t == gst.MESSAGE_TAG:
            keys = message.parse_tag().keys()
            tags = dict([ (key, message.structure[key]) for key in keys ])
            gtk.gdk.threads_enter()
            self.set_metadata( tags )
            gtk.gdk.threads_leave()

    def set_coverart( self, pixbuf ):
        self.cover_art.set_from_pixbuf(pixbuf)
        self.cover_art.show()
        self.has_coverart = True

    def set_metadata( self, tag_message ):
        tags = { 'title': self.title_label, 'artist': self.artist_label,
                 'album': self.album_label }
 
        cover_names = [ 'cover', 'cover.jpg', 'cover.png' ]
        size = [240,240] # maemo
        if not has_hildon:
            size = [130,130] # Desktop size

        if tag_message.has_key('image') and not self.has_coverart:
            value = tag_message['image']
            if isinstance( value, list ):
                value = value[0]

            pbl = gtk.gdk.PixbufLoader()
            try:
                pbl.write(value.data)
                pbl.close()
                pixbuf = pbl.get_pixbuf().scale_simple(
                    size[0], size[1], gtk.gdk.INTERP_BILINEAR )
                self.set_coverart(pixbuf)
            except:
                #traceback.print_exc(file=sys.stdout)
                pbl.close()

        if not self.has_coverart and self.filename is not None:
            for cover in cover_names:
                c = os.path.join( os.path.dirname( self.filename ), cover )
                if os.path.isfile(c):
                    try:
                        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(c, *size)
                        self.set_coverart(pixbuf)
                    except: pass
                    break

        tag_vals = dict([ (i,'') for i in tags.keys()])
        for tag,value in tag_message.iteritems():
            if tags.has_key(tag):
                tags[tag].set_markup('<big>'+value+'</big>')
                tag_vals[tag] = value
                tags[tag].set_alignment( 0.5*int(not self.has_coverart), 0.5)
                tags[tag].show()

        for tag_val in [ tag_vals['artist'].lower(), tag_vals['album'].lower() ]:
            if not tag_vals['title'].strip():
                break
            if tag_vals['title'].lower().startswith(tag_val):
                t = tag_vals['title'][len(tag_val):].lstrip()
                t = t.lstrip('-').lstrip(':').lstrip()
                tags['title'].set_markup('<span size="x-large">'+t+'</span>')
                break

    def demuxer_callback(self, demuxer, pad):
        adec_pad = self.audio_decoder.get_pad("sink")
        pad.link(adec_pad)
    
    def rewind_callback(self, w):
        if w == self.rewind_button:
            seconds = 10
        else:
            seconds = 60
        self.set_controls_sensitivity(False)
        pos_int = self.player.query_position(self.time_format, None)[0]
        seek_ns = max(0, pos_int - (seconds * 1000000000L))
        self.player.seek_simple(self.time_format, gst.SEEK_FLAG_FLUSH, seek_ns)

    def bookmarks_callback(self, w):    
        BookmarksWindow(self)

    def forward_callback(self, w):
        if w == self.forward_button:
            seconds = 10
        else:
            seconds = 60
        self.set_controls_sensitivity(False)
        pos_int = self.player.query_position(self.time_format, None)[0]
        seek_ns = pos_int + (seconds * 1000000000L)
        self.player.seek_simple(self.time_format, gst.SEEK_FLAG_FLUSH, seek_ns)
    
    def convert_ns(self, time_int):
        time_int = time_int / 1000000000
        time_str = ""
        if time_int >= 3600:
            _hours = time_int / 3600
            time_int = time_int - (_hours * 3600)
            time_str = str(_hours) + ":"
        if time_int >= 600:
            _mins = time_int / 60
            time_int = time_int - (_mins * 60)
            time_str = time_str + str(_mins) + ":"
        elif time_int >= 60:
            _mins = time_int / 60
            time_int = time_int - (_mins * 60)
            time_str = time_str + "0" + str(_mins) + ":"
        else:
            time_str = time_str + "00:"
        if time_int > 9:
            time_str = time_str + str(time_int)
        else:
            time_str = time_str + "0" + str(time_int)
            
        return time_str


def run(filename=None):
    session_bus = dbus.SessionBus(mainloop=dbus.glib.DBusGMainLoop())
    bus_name = dbus.service.BusName('org.panucci', bus=session_bus)    
    GTK_Main(bus_name, filename)
    gtk.gdk.threads_init()
    gtk.main()
    # save position manager data
    pm.save()

if __name__ == '__main__':
    print 'WARNING: Use %s-wrapper to run %s.' % (sys.argv[0],sys.argv[0])
    print 'exiting...'
