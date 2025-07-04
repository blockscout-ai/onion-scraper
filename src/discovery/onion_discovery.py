import os
import re
import csv
import time
import socket
import random
import threading
import glob
import json
import logging
from datetime import datetime
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# ----------------------------
# Configuration
# ----------------------------
TOR_SOCKS_PROXY = "socks5h://127.0.0.1:9050"
TOR_CONTROL_PORT = 9051
TOR_CONTROL_PASSWORD = 'Jasoncomer1$'
CONTROL_TIMEOUT = 3

# Logging configuration
LOG_FILE = f"crawler_log_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"
PROGRESS_FILE = "crawler_progress.json"
RESTART_FILE = "crawler_restart.json"

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

SEED_URLS = [
    "http://4yr6xac6fvhi6mdwm6julwnvkrj5whw43l7txyv267dm37stsn7i3rid.onion",
    "http://hhfrdjsr5fmlt472abc3p7ztxkwus42v6vmmqud2vmi7ytnxtzne3eid.onion",
    "http://no6m4wzdexe3auiupv2zwif7rm6qwxcyhslkcnzisxgeiw6pvjsgafad.onion",
    "http://ahmiai45jeruhemta4pg344x3btevkhadp64f6zppk32nhxays6bw6ad.onion",
    "http://qg24mbrij6rzxr77eovjwjzw7zwn7brmegr3yvwvppj4vhdxeuezkdqd.onion",
    "http://l72eq4374qyp24oucz3ypksvsyrqqhtsqo2ystkp5iz62cysclfru7qd.onion",
    "http://iwsp5e76ah4qcvpptwmqnlmagkego76k2zfebthfkjeqmqpkbpfy7ead.onion",
    "http://light3232dmbbnigk34aeg2ef3j3uvnwkqsymunadh3to3vg4gpyeyid.onion",
    "http://breachdbsztfykg2fdaq2gnqnxfsbj5d35byz3yzj73hazydk4vq72qd.onion",
    "http://n3mihgtekvqkqvshh6zjxbyc6kzwdsbvwihmredugnzi2dtxknwf7had.onion",
    "http://searches7gwtdwrzrpczfosri3dwihqxvkacqfcxc5r6ku72ehra7bqd.onion",
    "http://iy3544gmoeclh5de6gez2256v6pjh4omhpqdh2wpeeppjtvqmjhkfwad.onion",
    "http://torchac4h5bchwcxnnl566u5uuaclrufmaecv7ll2n64aggzsy5of2yd.onion",
    "http://yihcjsbquauelucvtgx6itie5xsurz6tszx4weltbvfyyfn3fpkxzfid.onion",
    "http://metagerv65pwclop2rsfzg4jwowpavpwd6grhhlvdgsswvo6ii4akgyd.onion",
    "http://zb2jtkh4gxwyiuq36x2u7ubptxejg5snaqmosxsupx7esmnl4g47d3yd.onion",
    "http://tornadox5n4g7apkcr23yqyi66eltomazrfgkljy22ccajywd2jsihid.onion",
    "http://tz75oxijoo4scfngg7w3wj5i3czcpgwu7rc65vkrcgp5xzjmfzozfyid.onion",
    "http://publica6d3mkbqevzg6rdftngrzczxueaxgmrdqzkoxyfwpmlw6elfqd.onion",
    "http://mdz3bapx56l44mf6hody46xggrrpl535dgvqqmqxkupt6s5i47tsbjqd.onion",
    "http://v5xddqfu6cyy7pbnjgyo4epa2rnquocaewoxz45qnrvykyyw3ex7m7yd.onion",
    "http://lolipornrgrqfiuro7xs6lidbd6waqfjyvn3kbwlwa2b27tn4tlkpxid.onion",
    "http://serhackqsiawme7y6yeaead6pgxigqnivws4pqml3n5sume66g7l5fid.onion",
    "http://d4qhcwtsurrf5gkxtywc6tms47xeam2s44wzmft732qv55d7a66oldyd.onion",
    "http://kewgkvbzmjprghk2gv6otkxuyvn2gdnv4256uiumuykjio7nyo5k6rid.onion",
    "http://torbookpm6hjivuo2owdi2s5erd7todjoqlp2qsfvzztoe7wywpwaoid.onion",
    "http://3bbad7fao6wyfr3bdgeg4r4as2tvuneanwjs45iz47kg53mgwrvel5yd.onion",
    "http://yahooirqyxszdwot6gdkp237lj4nlw3jdlim2kl5cwj6wgosonqzunqd.onion",
    "http://onixxxxxbddwewhvktd5zf5s7arpkmkv3m7n4zorjxvfxl7zowhvseid.onion",
    "http://ng27owmagn5amdm7l5s3rsqxwscl5ynppnis5dqcasogkyxcfqn7psid.onion",
    "http://torbookpm6hjivuo2owdi2s5erd7todjoqlp2qsfvzztoe7wywpwaoid.onion",
    "http://af5vzhlmqv4g6ncy7kfdxdygbq55h5h67nw6ejq5qf5hmmooxvvrw5id.onion",
    "http://lucifermvqbrcpqsc57t6pm7vvcnk2ddyy7ffot3bpywr4qmdodsnhad.onion",
    "http://nr2dvqdot7yw6b5poyjb7tzot7fjrrweb2fhugvytbbio7ijkrvicuid.onion",
    "http://l72eq43l7dcwrgyzez6mwrje5ok3o6ylkrl3ajr7xpcfzmywfquzglid.onion",
    "http://hl2mjycmmejhtf52ealhygt246kkuuzwfth5z2irqwuk3r4lsfuoyxqd.onion",
    "http://torgolnpeouim56dykfob6jh5r2ps2j73enc42s2um4ufob3ny4fcdyd.onion",
    "http://ondexcyirrwd4vvvpylav4r6dojnxgckj7rwywcklsz7cjrm5ush4fyd.onion",
    "http://luciferpvnfmqku7agzmcdoskor536za5574qtyx2vhrnuozv5fla6ad.onion",
    "http://kyk2u4zgzyatogl4kpzgoxoyu7rp335iubemng52bwkca6mz55xacvad.onion",
    "http://tornetup5upc7np66snanbe4nodkbvcuyjroyzl6ljtuftinonc2uhyd.onion",
    "http://searchgf7gdtauh7bhnbyed4ivxqmuoat3nm6zfrg3ymkq6mtnpye3ad.onion",
    "http://torch4st4l57l2u2vr5wqwvwyueucvnrao4xajqr2klmcmicrv7ccaad.onion",
    "http://3xdayezuazor2oha4z33il6dlro5wxpvjofnuukebwms5gtnticygwad.onion",
    "http://zgphrnyp45suenks3jcscwvc5zllyk3vz4izzw67puwlzabw4wvwufid.onion",
    "http://tornetcitj73djxpcgdf4d6ukjonvijfxci4o5yfo6xlmcrqmympflqd.onion",
    "http://222222223bmct6m464moskwt5hxgz2hj2wbsh224oh4m3rfe6e7olhqd.onion",
    "http://ke2hyko4fkqk5mhyrhhy76ldqxmmolyodowescrnj64k3l7xyanj4fid.onion",
    "http://orealmvxooetglfeguv2vp65a3rig2baq2ljc7jxxs4hsqsrcemkxcad.onion",
    "http://lvqpvsourrzyz365goyr5pi4fpw5o4owpeehpf6utt6yumlfqpqkx4id.onion",
    "http://hologram6d4agtfbwkdtruigzo3l6wztcz5rg27rmh54qatyinqmzgid.onion",
    "http://oniondxjxs2mzjkbz7ldlflenh6huksestjsisc3usxht3wqgk6a62yd.onion",
    "http://haystak5anm6d3u6uyw35fej6wdhcf7jq4jvs7osfutley4wmuom6eqd.onion",
    "http://v5xddqfu6cyy7pbnjgyo4epa2rnquocaewoxz45qnrvykyyw3ex7m7yd.onion",
    "http://2222222u6b2hd4vc6lgbz3gzxt73dn4gi3dtco5moim7qf2m34ka4tid.onion",
    "http://torch4srxkk2lvxwyrb2zaq3sw7ztc5bxqv4xpqc5gmmv5x6h2nts3qd.onion",
    "http://luciferpfonohwmukmwua6cmnsxh6ufo6hjclrb6omd45hkvlbnja4ad.onion",
    "http://5undviuzu4z2h6ayqkxuvjnv5n343vme5ei7wdxsjaqphsydrt3mk3yd.onion",
    "http://rczml4qfhub5j4ubtr5a6ndwilpbewz7zluhnasfh4poe3vnesuq4wad.onion",
    "http://idexy5uaqeeywyhegockjnesn77wugqclbkt3xvadln567k3zf32cvyd.onion",
    "http://dnukpoba7hhkkezgnmfohqvsqo4htstyszi4o67vxz2cyriqpdrsyuqd.onion",
    "http://orealmvxetzsvtnc3e34vvwu2eog3pnum6xmlzzgwfflbwm33oghutyd.onion",
    "http://publica6d3mkbqevzg6rdftngrzczxueaxgmrdqzkoxyfwpmlw6elfqd.onion",
    "http://matesea7myfqb62sbjtpx3dfchalnpf2b4ppw52lzuxwvlbtj2kb3nqd.onion",
    "http://i2poulge3qyo33q4uazlda367okpkczn4rno2vjfetawoghciae6ygad.onion",
    "http://srtwuinx6xvgmwtu6xfgjqa35orqxi4obtw6o7gspfubruqnmi54m3qd.onion",
    "http://good5nycto5lom7qqyx3pfn26wvmc6trq536zd752idmfbatnd6i36qd.onion",
    "http://bt4gcomcf45mceic277o3goxvizgh6yj6vazoj4o63wfqujzykzdavyd.onion",
    "http://whereissky27lxfdrs7ct7a5ievor3tl67qi77rv5luga7wod5jf2mad.onion",
    "http://3bbad7fauom4d6sgppalyqddsqbf5u5p56b5k5uk2zxsy3d6ey2jobad.onion",
    "http://haystak2wfqmtftctncw7hj6p6glevgffy5b7uios7fypaocbucmehad.onion",
    "http://777topalcjomgpfmxbgtnpodgkkifm4qoqjzbc7thpmtq3k4sksmj3yd.onion",
    "http://tor66sewwizhwfrnrphw53cthpvxj6hr4copuh6zd7lgkoo3cqcmj7yd.onion",
    "http://zgphrnyrdzssggdzqo3vq3gc4olkigf646pcv5mix3uzorl66dug6nad.onion",
    "http://orealmvxlcjivdz7faenxr5z2ezh22qnb33qytsabmbfnsel4s3xg7ad.onion",
    "http://p3yz4rpfiorn5nogjiopxrb2iacv7fgseyl6exnpptogrg5rl3sq4aad.onion",
    "http://bobby64o7dhnkkgumhshw3lwosqkragllyv33nd6zgqk7lzgz3sevrqd.onion",
    "http://zozcz66bnt6s2qzhnyajv75uwfmkd7i35cnaeht6e642imaqzdmdcwid.onion",
    "http://5qqrlc7hw3tsgokkqifb33p3mrlpnleka2bjg7n46vih2synghb6ycid.onion",
    "http://jhwvlvwnmu6lvwmjabrctdhbtfplw3p7trxmdjqfazkf2b2vgz7pscid.onion",
    "http://bobby64o755x3gsuznts6hf6agxqjcz5bop6hs7ejorekbm7omes34ad.onion",
    "http://l337xdarkkaqfwzntnfk5bmoaroivtl6xsbatabvlb52umg6v3ch44yd.onion",
    "http://publicagv4whofakenfr4b7smjzahr7jsikfgtthshn2e6fyk6m4rnid.onion",
    "http://wbr4bzzxbeidc6dwcqgwr3b6jl7ewtykooddsc5ztev3t3otnl45khyd.onion",
    "http://venusoswti4gxjlxplnx66syjiv4veexixh7qkbjbmgf7nmctagqvwqd.onion",
    "http://2fd6cem3xk6fkkynap3ewhzy2rybrmeigu2lm2bxcoaayxfka2df7syd.onion",
    "http://rczml4qtgokopf6w2stsebr4jbhgdxyetikrlfwvuylesbnqargduryd.onion",
    "http://z4yehlam3lye6nff7nzrlzkkerow6agotxnkfm5etgpowy4rirgmq4ad.onion",
    "http://anima4fwxjqryiqd27advfotgzd3cpa3g4stn32s5wcimii7mebh7nyd.onion",
    "http://danexio627wiswvlpt6ejyhpxl5gla5nt2tgvgm2apj2ofrgm44vbeyd.onion",
    "http://epatmtofq4oipqzvqzsjf3htieqqlafkahkdleae2rgecnmf6wzhxzqd.onion",
    "http://kaizerwffm7osj37ejkccesc3doja3zstbawi7wcykaogoqx7pcyaoad.onion",
    "http://search7tdrcvri22rieiwgi5g46qnwsesvnubqav2xakhezv4hjzkkad.onion",
    "http://bt4gcomonjoqfebo45bu3swksfehtsli6obxgnp33s6zt3vd7tmejryd.onion",
    "http://drugybsencwyzc6sw6nzecuoavw5cvmqq2dhyojqaghfuve2dmzs4jqd.onion",
    "http://uniquelidkc3s2dussvwp473o6dtcaireq2ivgbfts6oh3n7427ojlad.onion",
    "http://deeeepqgithvfzcarnongujexpp2fpji3hlz2fdtpyhnjll6j4tjlsqd.onion",
    "http://leaklook7mhf6yfp6oyoyoe6rk7gmpuv2wdk5hgwhtu2ym5f4zvit7yd.onion",
    "http://fyonionswg5tb4ndveiu7gpwyashw4jhti5jtqfljwgx23y6ai2ffaqd.onion",
    "http://darksidthvquha52o4fzvtap4ticaoh4sboobywadzkvcbjzhtapadyd.onion",
    "http://searchpie7fejn4wctzm6fgm6oz5vnziltfzzuec6b4qmkr3wrqaoqqd.onion",
    "http://ke2hykova5nnfq72xuz3f52ui4n4qmmeom5asn32ns5tjqasa3kdxfyd.onion",
    "http://tz75oxijoo4scfngg7w3wj5i3czcpgwu7rc65vkrcgp5xzjmfzozfyid.onion",
    "http://no6m4wzdyspwokghitdzqwnjev5e32gfj5ndlhpuck4rq2ojsvrdg7id.onion",
    "http://mdz3bapx56l44mf6hody46xggrrpl535dgvqqmqxkupt6s5i47tsbjqd.onion",
    "http://g673k27fdje2lmyhuhaivlsj42d6ttldk47wexg5qpygxtz3euo74dyd.onion",
    "http://shrlk7x3mjmqvbwlozt3tyu4p4hbnbe62jmkdcoakk3f37i7c5hwn2yd.onion",
    "http://juhanurbgyvngjxziyjaz6pg6bhjjzfiatlfjen2qpb3orv3j5oiseyd.onion",
    "http://gszllv64wrzqcf4p7mt2jwtfbrj425usweqqi44z2ujfn5f7jan4s6id.onion",
    "http://tor66sekisdblpgxdbhjnewzhodzcadifz52272uewey77jfuxwoxtyd.onion",
    "http://ijridx42bzzelztznz7lzeoule4ug45qmtmvhffotdetj6xxaxi54ryd.onion",
    "http://btdigggok4d4pz6e3gdvj4ghdnmzhwctuff2jnh4gfanaqsd4omj3oqd.onion",
    "http://oniwayzz74cv2puhsgx4dpjwieww4wdphsydqvf5q7eyz4myjvyw26ad.onion",
    "http://tornetupfu7gcgidt33ftnungxzyfq2pygui5qdoyss34xbgx2qruzid.onion",
    "http://ondexcylc2qrovrn44eyrksxmssncvyailvov5pi7pfh4aj7zjxkx3qd.onion",
    "http://orealmvo7j6kfixcz7x3yjmlc2szw3j3qugcfuwas2trtnt6mbp7v2ad.onion",
    "http://l72eq4374qyp24oucz3ypksvsyrqqhtsqo2ystkp5iz62cysclfru7qd.onion",
    "http://gaklwru23b5xyphfpclyputhheudrcxfjac3cusn6kavsy46a7mqlzid.onion",
    "http://gdark5np65mxg3v6lq4sdleiobntkyw3y3e6u26xe3vtgpkxm2efhkqd.onion",
    "http://torchoeyj64wyvloopauman6e7tan7xwgadxscrflwn3b66u3apkf2id.onion",
    "http://wbr4bzzxdha355maxubylpznt5oxab4gv46qpfd7y32dsj4j5w6qvgid.onion",
    "http://avop253wzsdx76p267yu22n26ouaxuqd427s35doi2ojrqesrfyeafad.onion",
    "http://nr2dvqdo6z664ecn77xasgj6xa6yy4bpjkmdqreyigkkhwoirnesz2qd.onion",
    "http://metageraxerjzaeyxh763nrti6h7gkoqahiwzzvz3qwiahu72iskncyd.onion",
    "http://darksid3e3id2df26prfehrluo3tk2w7cqen55etarazrgboaqywbnyd.onion",
    "http://r6ogx3wljq5lmmcnnoodf7ova2jh5ziatvfcibxs6u5oiitgo5xiytyd.onion",
    "http://qxcrvqhmbgyo5bi4bnkesg2ydpggkolrfjh7kogo7rkz4k5wv5adoeqd.onion",
    "http://torchylezad54ysdudl4ljtiachjoqbwssctaqv2p425crwkk3tfl4qd.onion",
    "http://juhanurmc2d3qntsvgirs2jakvjhcjd2ng2omq5oiq2oolcdoqand2id.onion",
    "http://zsjvvfabm5v45fcokhfraqxvuggijhpmaybxr3fhokmm7wdnni6tyhad.onion",
    "http://iy3544gmoeclh5de6gez2256v6pjh4omhpqdh2wpeeppjtvqmjhkfwad.onion",
    "http://search7fzumhb75f45nkk25ka4pzbaoxmqkkimt6cjxs7dr4zyajr2qd.onion",
    "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion",
    "http://darkhuntxyxutk3cda4eogyvbcdcmsijv4i2dwtkfoeb6ggwzz7ke3qd.onion",
    "http://gk7kp5gcmtbycxdnm2hgcsx55amuk3cfoamq7chrdbg2hxaa3wnb3xqd.onion",
    "http://amnesiagrn6fgm6dia434i4vri6wugxxiknrius73rquhm3a5p2cyuad.onion",
    "http://drugidjjstv6lklmqeqd7eypjjtc24niaskpivrwa5wmb3vwd2ndwgyd.onion",
    "http://bkge4lkx2gc7pkmi5uoajz4btt23p5i6hh5wyltlmotbsiprpjodriqd.onion",
    "http://af5vzhlwr4sqxzixsreaixia4jom2sifj7jt37tjiinbvkkbrrzchwid.onion",
    "http://xhqthou6scpfnwjyzc3ekdgcbvj76ccgyjyxp6cgypxjlcuhnxiktnqd.onion",
    "http://searchongi5is5rlcy4xjey345ezyvcleswueazb2jq7cmqvit7pgtad.onion",
    "http://torchqfmuhpqteg5nww33wztcfxcly2rl3kwsk6zxja7gi5awgsk7qad.onion",
    "http://ov34bg7wnacid2feuwkemp46t7r4ib4adb36h3c7j4na5sjrfcypp5id.onion",
    "http://iwsp5e76ah4qcvpptwmqnlmagkego76k2zfebthfkjeqmqpkbpfy7ead.onion",
    "http://tor66sewef5qewx6yvxg5rcsutn3ejzuwppc6dtoljwb5zxdkbo7kwqd.onion",
    "http://7o3idg6d5uqhnwi6ond54ig364l5gtyzwowxqpbie6ofoikmuzmk3zad.onion",
    "http://navigatorf3jbtpd65e6dobehgbcz6erpzwhzffuylgiqg4hcornygad.onion",
    "http://46xkbdr7vrj3j2roxxtfhtz53bvpqqo2cjf6tmlhw7yjttrvwadbvdid.onion",
    "http://breachdbsztfykg2fdaq2gnqnxfsbj5d35byz3yzj73hazydk4vq72qd.onion",
    "http://light3232mz4dnbomv2dxyffonsltcz7kvo6uvxvzbxrvrw5ygozxfqd.onion",
    "http://n3mihgtekvqkqvshh6zjxbyc6kzwdsbvwihmredugnzi2dtxknwf7had.onion",
    "http://thedude75pphneo4auknyvspskdmcj4xicbsnkvqgwhb4sfnmubkl5qd.onion",
    "http://p6xkj5w2iim5ho5xd4ngn26g35finfclbui66sahlr63w5ylqqn67iyd.onion",
    "http://torchdeedp3i2jigzjdmfpn5ttjhthh5wbmda2rr3jvqjg5p77c54dqd.onion",
    "http://clszzn45huuh566ic546sxoesdnobjfeoyglalxbgpdhdlowyuwpi7yd.onion",
    "http://dztu5cvxtogtn4kowlpmr6z5yia2r7lysg3dktja5fckujqqavmv6zyd.onion",
    "http://breachdflrmzrvlpsu64rywjchin6e5hsndjelbv6nq2jwodtoxz5vid.onion",
    "http://otql7uonr5avbyjwsff5afss4cfdpoik7f5imn74k3m5oq4z4hs5tjyd.onion",
    "http://zb2jtkhnbvhkya3d46twv3g7lkobi4s62tjffqmafjibixk6pmq75did.onion",
    "http://apwjzyehv5lkv5rwoqvsi7sedko5icxji7f2ybxrots2scolx34oeyid.onion",
    "http://iwsp5e7wnrhtmpjsjszaarnyk63kcdkbmn6njxisgdcjc4xho77imbid.onion",
    "http://jd5sh2futbgdzhk2u4s4oogupeeog6tjtqhkpw2hh6a2pt4tqoomurad.onion",
    "http://clszzn47y57uwkrgnfc7wllalvodopzqrp4spb6zbz2t3ulxngcfqsad.onion",
    "http://drugmqf2lm7u3v7hffw77yk7qqeif7nyslrlynzimakkf3t5ru75suid.onion",
    "http://torchachugey4if5zy2ao74wbddmmsosmvs5mr76l2kph4cevbl5btid.onion",
    "http://orealmvdwjfwlyzplgqzbs4w3bhbvmra7aptex2ndlqtxqqn7rhdzlad.onion",
    "http://iy3544gmjfwqcy3z6jxjjj4hby4rj5gpslupnqwt5mra4hguvge5hyyd.onion",
    "http://light32oppwtsuqbdzysloalbsqksjfoau237z7qzbujcbbklgfa25id.onion",
    "http://yovnzyvt3i77rh5llcidmfjkyqvr5bnwz6c27ixj3prxmp4psm3zlxad.onion",
    "http://zoozle4qpbnectvv3ndvcalisaka65kven4xiomvs55otfnuaxewa2yd.onion",
    "http://ql3fkzwg67z6y2ixllpzspa6fpuhstdjghza3yd3ah62jwu26iszooad.onion",
    "http://heypoh3nsi3w2rqvqikcwlpwpxy447oteivvpn7rkor5plw7fsaobgyd.onion",
    "http://breachdb7r5fusv54wbqgfrmtqcle647ybi7jyi2b2btqyraioox3wid.onion",
    "http://haystak3xdnjbmljnspmgdnsnxukhdyoajxftjrbku2nb2agzetgkhid.onion",
    "http://igdnewsfiu4tfxvecxjls3txdfdmukke6eho5qvxh2h4rbuuxd6leoyd.onion",
    "http://anima4ffe27xmakwnseih3ic2y7y3l6e7fucwk4oerdn4odf7k74tbid.onion",
    "http://6pxxjp7l2fervwwxiwr7kkheoed2gch6c2kkpionsjckk2molias2cad.onion",
    "http://zoozle4zosadpgos6dsasecupniqyjjpuxojtarscmqqullbeh4ohqad.onion",
    "http://torchrc24stufqav4rl2fxlce3jjvzlpdutomaukdykpcjoyzfqzuhyd.onion",
    "http://r4tveqfjxtiivneennth5ijjynjadr2t4ip7dshn47i7nhenrftti6yd.onion",
    "http://ondexa2tepkro7puyvafr2vfo3uofq3ipapqecgurshjzpbruzznyoyd.onion",
    "http://3gez2dfuf4y7buo33hq2xkhjiy6jfxfmszmipjbvfwo4jz6gk4qi4pid.onion",
    "http://oniondxinq4wd3pg7bkjyi3ipl6eivcokderve7qg4ga5aomklcgoyid.onion",
    "http://torchdeeqbseeuhg2by42gkkpnwye7dzs7oo2oql7hikba73gxfiz7yd.onion",
    "http://searches7gwtdwrzrpczfosri3dwihqxvkacqfcxc5r6ku72ehra7bqd.onion",
    "http://mond5tycmmi52mkvqi32bpadj3nr3skkfwtjjdv5n57i7tfej5paf5qd.onion",
    "http://2fd6cemt4gmccflhm6imvdfvli3nf7zn6rfrwpsy7uhxrgbypvwf5fad.onion",
    "http://fyonionsqkae65mfxsgvp3fu4q2aegdrz3dh5ocjlbjrfybpqywgshad.onion",
    "http://venusoseaqnafjvzfmrcpcq6g47rhd7sa6nmzvaa4bj5rp6nm5jl7gad.onion",
    "http://luciferxipty64zukypvpqudgwkuscrfinhmhery7gqefp2mi2xjllid.onion",
    "http://5iuofm75d4adueyshmybjrxv2ks7l7caxcueijxzmhdulag4q3jojgid.onion",
    "http://qg24mbrij6rzxr77eovjwjzw7zwn7brmegr3yvwvppj4vhdxeuezkdqd.onion",
    "http://digitalx5kznjsvcjka77td7yrbyytbtd37dareh4axoajlxff77sbyd.onion",
    "http://6ht5cuex7h2e2okzyculgduscxdrbaznxy45xsanigrgml2iuuifbkyd.onion",
    "http://2222222atttb4bsukqadukoexd7iwa6laoiircn3xvjy67qw4wn45nqd.onion",
    "http://zf6biopcnnxpkgqtbluotac4t5kjqb4k36as4k5gprg7hykxq6iqdgqd.onion",
    "http://okuqm7cak24fo2algfsauuxnfyh77nzvtbp77nfbuukh6m6f3d6exsyd.onion",
    "http://onixxxx7h6cvl5srjuoezvp7xb4y6b5hkcra2sqrqnypxnbqrwcktvqd.onion",
    "http://2fd6cemtduq7xvmaexqhrx7reupcfztxwvchhzlw7xalixwrmm5ssoid.onion",
    "http://torchac4wwv4sd3qt73xjxvz6wxiande4mhsvbhi4icsui7lgwh4kbqd.onion",
    "http://ov34bg755fzbtpb73j46nqgvwzpnombyzp6i6rpbtxwxw6k6izp27qqd.onion",
    "http://serhackqsiawme7y6yeaead6pgxigqnivws4pqml3n5sume66g7l5fid.onion",
    "http://btdigggink2pdqzqrik3blmqemsbntpzwxottujilcdjfz56jumzfsyd.onion",
    "http://amnesia7u5odx5xbwtpnqk3edybgud5bmiagu75bnqx2crntw5kry7ad.onion",
    "http://5kxnxa5nm5gzs5ex6toj4mva5uqeyunwbu36qm3delhfoes2d7hfdiad.onion",
    "http://darksid3f3ggicny772rvdmrcgfbtixsyjpdgm6unh5qci6r24ukg4qd.onion",
    "http://j6i3blst2fabntc4fyd2rpl3phk3rxpvc5oaxyzrpami36af3hq42fad.onion",
    "http://navigatorqaqude2gxgu7lvpe76drpufslcrablvclze4qc4n2asj7yd.onion",
    "http://ce6s66jcw24oatp6meb6fpg5aakvgexjjscdpleylnmflvparcgg2eyd.onion",
    "http://5qqrlc7hgp4cbgu5ls44fqf5hhtd4putpzu3oiaksu6mpkuecdh6ziad.onion",
    "http://ondexh46xin5wsjsz44b3jqucd4ytzz5l7pbcfpmzm5ejamfnol7mpyd.onion",
    "http://6tvoq5fn6zdahzuc5suqzw6ypcbw5cxm2ss3sqhtu6voffu4xf2k4zid.onion",
    "http://gaklwru23azbl753erocd63e7ez3vzgvv2l6vwvcsztldle5qvsxkoid.onion",
    "http://hbfkm3227ktso5ni4royouhmwhwovt2dakks5jp7gaj6xincy3yju6qd.onion",
    "http://6pxxjp7iwjbvtrfv3qqgz36zm6nnovi3xujepycve3n4jirg5vpmorad.onion",
    "http://searchgwgb5pty6suoelk2zcsfo5wutslsy2vylu4sgbizregas476qd.onion",
    "http://dqp5kblhl3a4qvt7tbppgx4c4wxsnoelgmvsqrdbgx4kghhu7s4b6iid.onion",
    "http://oniwayzzq4cwp7uoc3mhzn3hmsnit3wxqksrubno4v3npr7ssp4szwyd.onion",
    "http://6evmkmg4p6r354tjdgvjjzej32mnin6mdfi6zm3lu6qqpulqfvmkfsid.onion",
    "http://ondexcylxxxq6vcc62l3r2m6rypohvvymsvqeadhln5mjo73pf6ksjad.onion",
    "http://strangevjf5wst4nrvuv7wfxemx4hi2qp4sfnmnirfayufhtzzwedjqd.onion",
    "http://4vcyhfdmnjb4lr223tunzcmpf4r3kv4y33npwziy7g5wsf55ye6mmdid.onion",
    "http://4yr6xac6fvhi6mdwm6julwnvkrj5whw43l7txyv267dm37stsn7i3rid.onion",
    "http://t7wq764zw4czug2xm5gqpnc7jcpgdnsqs7c4os3ifh5fz4umnr3mpyyd.onion",
    "http://2osfrf6zh7nbpho3esn7qyf6s2svtzxjtjrvivgkxmyc2sht2lym4pyd.onion",
    "http://breachdp643betkmryssir6kbr74vx2wiit5z62nwomkzpi7rdcqvgad.onion",
    "http://loliporntdgonaeqnh6istmhzay2otcw3zyfytnb4chnkefaaa2tb6ad.onion",
    "http://d4qhcwtsurrf5gkxtywc6tms47xeam2s44wzmft732qv55d7a66oldyd.onion",
    "http://notevilmtxf25uw7tskqxj6njlpebyrmlrerfv5hc4tuq7c7hilbyiqd.onion",
    "http://dwddht3rotbsqwzq3e34m3xancnjcdteqzfcxvfabhxa6jqjizkoilid.onion",
    "http://dpbcqrjpdjrdcmiws6gs6fvyhhcrwf2egaqbmt6l36l2nedgam2cfrad.onion",
    "http://stealth5wfeiuvmtgd2s3m2nx2bb3ywdo2yiklof77xf6emkwjqo53yd.onion",
    "http://nerdvpn4iln4didgzcw7pgvjv4p3pwn3e3dq732oxwidfv6bacnyuvad.onion"
]

# Search engine URL patterns for keyword searches
SEARCH_ENGINE_PATTERNS = {
    # Primary working search engines
    "torch": "http://torchdeedp3i2jigzjdmfpn5ttjhthh5wbmda2rr3jvqjg5p77c54dqd.onion/?q={}",
    "searchongi": "http://searchongi5is5rlcy4xjey345ezyvcleswueazb2jq7cmqvit7pgtad.onion/?q={}",
    "strange": "http://strangevjf5wst4nrvuv7wfxemx4hi2qp4sfnmnirfayufhtzzwedjqd.onion/?q={}",
    "smsawhx": "http://smsawhxdqsarz5hdveltgr2qyai64zyxaea5rzeo3przfqqj7izay2qd.onion/?q={}",
    "6evmkmg": "http://6evmkmg4p6r354tjdgvjjzej32mnin6mdfi6zm3lu6qqpulqfvmkfsid.onion/?q={}",
    "juhanurmih": "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/?q={}",
    "juhanurmc": "http://juhanurmc2d3qntsvgirs2jakvjhcjd2ng2omq5oiq2oolcdoqand2id.onion/?q={}",
    "4yr6xac7": "http://4yr6xac736rnkf62ku7t2udo7mijbrkoqlvjudmdgm4tgxxswaadr7ad.onion/?q={}",
    "otql7uon": "http://otql7uonr5avbyjwsff5afss4cfdpoik7f5imn74k3m5oq4z4hs5tjyd.onion/?q={}",
    "amnesia7kx": "http://amnesia7kx7gcdhuaykmlv5jdget57kbeplowfeezjnwdt67jrehgnid.onion/?q={}",
    "amnesia7u5": "http://amnesia7u5odx5xbwtpnqk3edybgud5bmiagu75bnqx2crntw5kry7ad.onion/?q={}",
    "anima4fw": "http://anima4fwxjqryiqd27advfotgzd3cpa3g4stn32s5wcimii7mebh7nyd.onion/?q={}",
    "apex6bo5": "http://apex6bo5gwavylpwgvdimbjb7oilq3if3r3kx5idh75lamga3wugthid.onion/?q={}",
    "bobby64o7": "http://bobby64o755x3gsuznts6hf6agxqjcz5bop6hs7ejorekbm7omes34ad.onion/?q={}",
    "btdigggink": "http://btdigggink2pdqzqrik3blmqemsbntpzwxottujilcdjfz56jumzfsyd.onion/?q={}",
    "dqp5kblm": "http://dqp5kblma4l4rjytkc2v4qelikvp42wh4gxkp2yxn24vobmh2vtkdnad.onion/?q={}",
    "danexio6": "http://danexio627wiswvlpt6ejyhpxl5gla5nt2tgvgm2apj2ofrgm44vbeyd.onion/?q={}",
    "qg24mbrij": "http://qg24mbrij6rzxr77eovjwjzw7zwn7brmegr3yvwvppj4vhdxeuezkdqd.onion/?q={}",
    "darksid3f3": "http://darksid3f3ggicny772rvdmrcgfbtixsyjpdgm6unh5qci6r24ukg4qd.onion/?q={}",
    "darksid3e3": "http://darksid3e3id2df26prfehrluo3tk2w7cqen55etarazrgboaqywbnyd.onion/?q={}",
    "r6ogx3wl": "http://r6ogx3wljq5lmmcnnoodf7ova2jh5ziatvfcibxs6u5oiitgo5xiytyd.onion/?q={}",
    "search7fzum": "http://search7fzumhb75f45nkk25ka4pzbaoxmqkkimt6cjxs7dr4zyajr2qd.onion/?q={}",
    "ov34bg75": "http://ov34bg755fzbtpb73j46nqgvwzpnombyzp6i6rpbtxwxw6k6izp27qqd.onion/?q={}",
    "good5nyct": "http://good5nycto5lom7qqyx3pfn26wvmc6trq536zd752idmfbatnd6i36qd.onion/?q={}",
    "2fd6cem3": "http://2fd6cem3xk6fkkynap3ewhzy2rybrmeigu2lm2bxcoaayxfka2df7syd.onion/?q={}",
    "ke2hykov": "http://ke2hykova5nnfq72xuz3f52ui4n4qmmeom5asn32ns5tjqasa3kdxfyd.onion/?q={}",
    "okuqm7ca": "http://okuqm7cak24fo2algfsauuxnfyh77nzvtbp77nfbuukh6m6f3d6exsyd.onion/?q={}",
    "fyonionsw": "http://fyonionswg5tb4ndveiu7gpwyashw4jhti5jtqfljwgx23y6ai2ffaqd.onion/?q={}",
    "zb2jtkh": "http://zb2jtkhnbvhkya3d46twv3g7lkobi4s62tjffqmafjibixk6pmq75did.onion/?q={}",
    "haystak2w": "http://haystak2wfqmtftctncw7hj6p6glevgffy5b7uios7fypaocbucmehad.onion/?q={}",
    "nr2dvqdo": "http://nr2dvqdot7yw6b5poyjb7tzot7fjrrweb2fhugvytbbio7ijkrvicuid.onion/?q={}",
    "i2poulge": "http://i2poulge3qyo33q4uazlda367okpkczn4rno2vjfetawoghciae6ygad.onion/?q={}",
    "whereissky": "http://whereissky27lxfdrs7ct7a5ievor3tl67qi77rv5luga7wod5jf2mad.onion/?q={}",
    "ng27owmag": "http://ng27owmagn5amdm7l5s3rsqxwscl5ynppnis5dqcasogkyxcfqn7psid.onion/?q={}",
    "igdnews": "http://igdnewsfiu4tfxvecxjls3txdfdmukke6eho5qvxh2h4rbuuxd6leoyd.onion/?q={}",
    "breachdp6": "http://breachdp643betkmryssir6kbr74vx2wiit5z62nwomkzpi7rdcqvgad.onion/?q={}",
    "6evmkmg44": "http://6evmkmg44iyut2s2zy4dtepdkya5l6qadvoq6hc5amaqmswl2rgkpoad.onion/?q={}",
    "light3232": "http://light3232dmbbnigk34aeg2ef3j3uvnwkqsymunadh3to3vg4gpyeyid.onion/?q={}",
    "luciferpv": "http://luciferpvnfmqku7agzmcdoskor536za5574qtyx2vhrnuozv5fla6ad.onion/?q={}",
    "metagerv6": "http://metagerv65pwclop2rsfzg4jwowpavpwd6grhhlvdgsswvo6ii4akgyd.onion/?q={}",
    "clszzn45": "http://clszzn45huuh566ic546sxoesdnobjfeoyglalxbgpdhdlowyuwpi7yd.onion/?q={}",
    "3gez2dfu": "http://3gez2dfuf4y7buo33hq2xkhjiy6jfxfmszmipjbvfwo4jz6gk4qi4pid.onion/?q={}",
    "notevilmt": "http://notevilmtxf25uw7tskqxj6njlpebyrmlrerfv5hc4tuq7c7hilbyiqd.onion/?q={}",
    "drugybsen": "http://drugybsencwyzc6sw6nzecuoavw5cvmqq2dhyojqaghfuve2dmzs4jqd.onion/?q={}",
    "5qqrlc7h": "http://5qqrlc7hw3tsgokkqifb33p3mrlpnleka2bjg7n46vih2synghb6ycid.onion/?q={}",
    "zgphrnyp": "http://zgphrnyp45suenks3jcscwvc5zllyk3vz4izzw67puwlzabw4wvwufid.onion/?q={}",
    "kewgkvbz": "http://kewgkvbzmjprghk2gv6otkxuyvn2gdnv4256uiumuykjio7nyo5k6rid.onion/?q={}",
    "mdz3bapx": "http://mdz3bapx56l44mf6hody46xggrrpl535dgvqqmqxkupt6s5i47tsbjqd.onion/?q={}",
    "oniwayzz": "http://oniwayzz74cv2puhsgx4dpjwieww4wdphsydqvf5q7eyz4myjvyw26ad.onion/?q={}",
    "p6xkj5w2": "http://p6xkj5w2iim5ho5xd4ngn26g35finfclbui66sahlr63w5ylqqn67iyd.onion/?q={}",
    "onixxxxx": "http://onixxxxxbddwewhvktd5zf5s7arpkmkv3m7n4zorjxvfxl7zowhvseid.onion/?q={}",
    "22222222": "http://222222223bmct6m464moskwt5hxgz2hj2wbsh224oh4m3rfe6e7olhqd.onion/?q={}",
    "lolipornr": "http://lolipornrgrqfiuro7xs6lidbd6waqfjyvn3kbwlwa2b27tn4tlkpxid.onion/?q={}",
    "lolipornt": "http://loliporntdgonaeqnh6istmhzay2otcw3zyfytnb4chnkefaaa2tb6ad.onion/?q={}",
    "u5b722sg": "http://u5b722sge6bfllcze53ypta2le2ffiuwibqdqaa7obh5w7zbdo6sarqd.onion/?q={}",
    "epatmtof": "http://epatmtofq4oipqzvqzsjf3htieqqlafkahkdleae2rgecnmf6wzhxzqd.onion/?q={}",
    "ijridx42": "http://ijridx42bzzelztznz7lzeoule4ug45qmtmvhffotdetj6xxaxi54ryd.onion/?q={}",
    "jhwvlvwz": "http://jhwvlvwzdhnk66lf3jlr3pi52vjm53giwckrlc2zov2jga57m5qq5qid.onion/?q={}",
    "zsjvvfab": "http://zsjvvfabm5v45fcokhfraqxvuggijhpmaybxr3fhokmm7wdnni6tyhad.onion/?q={}",
    "t7wq764z": "http://t7wq764zw4czug2xm5gqpnc7jcpgdnsqs7c4os3ifh5fz4umnr3mpyyd.onion/?q={}",
    "ondexcyir": "http://ondexcyirrwd4vvvpylav4r6dojnxgckj7rwywcklsz7cjrm5ush4fyd.onion/?q={}",
    "ondexa2te": "http://ondexa2tepkro7puyvafr2vfo3uofq3ipapqecgurshjzpbruzznyoyd.onion/?q={}",
    "publicagv": "http://publicagv4whofakenfr4b7smjzahr7jsikfgtthshn2e6fyk6m4rnid.onion/?q={}",
    "publica6d": "http://publica6d3mkbqevzg6rdftngrzczxueaxgmrdqzkoxyfwpmlw6elfqd.onion/?q={}",
    "iwsp5e7w": "http://iwsp5e7wnrhtmpjsjszaarnyk63kcdkbmn6njxisgdcjc4xho77imbid.onion/?q={}",
    "iwsp5e76": "http://iwsp5e76ah4qcvpptwmqnlmagkego76k2zfebthfkjeqmqpkbpfy7ead.onion/?q={}",
    "ahmiavpt": "http://ahmiavptbjnubgitmgooytrieoxj4dml7ufc73lox2jzelgtcyjwmjyd.onion/?q={}",
    "serhackqs": "http://serhackqsiawme7y6yeaead6pgxigqnivws4pqml3n5sume66g7l5fid.onion/?q={}",
    "dpbcqrjp": "http://dpbcqrjpdjrdcmiws6gs6fvyhhcrwf2egaqbmt6l36l2nedgam2cfrad.onion/?q={}",
    "6pxxjp7i": "http://6pxxjp7iwjbvtrfv3qqgz36zm6nnovi3xujepycve3n4jirg5vpmorad.onion/?q={}",
    "drugidjj": "http://drugidjjstv6lklmqeqd7eypjjtc24niaskpivrwa5wmb3vwd2ndwgyd.onion/?q={}",
    "stealth53": "http://stealth53py46pyoxvtappchzplxiadqlrhxxelojegtkimuft3e2cid.onion/?q={}",
    "stealthwdu": "http://stealthwduyals3krxqizgoarfbvliftof4po52ywabrmjy5m6ebzmyd.onion/?q={}",
    "no6m4wzd": "http://no6m4wzdyspwokghitdzqwnjev5e32gfj5ndlhpuck4rq2ojsvrdg7id.onion/?q={}",
    "orealmvx": "http://orealmvxlcjivdz7faenxr5z2ezh22qnb33qytsabmbfnsel4s3xg7ad.onion/?q={}",
    "searchgwgb": "http://searchgwgb5pty6suoelk2zcsfo5wutslsy2vylu4sgbizregas476qd.onion/?q={}",
    "bt4gcomc": "http://bt4gcomcf45mceic277o3goxvizgh6yj6vazoj4o63wfqujzykzdavyd.onion/?q={}",
    "l337xdar": "http://l337xdarkkaqfwzntnfk5bmoaroivtl6xsbatabvlb52umg6v3ch44yd.onion/?q={}",
    "idexy5ua": "http://idexy5uaqeeywyhegockjnesn77wugqclbkt3xvadln567k3zf32cvyd.onion/?q={}",
    "uniquelid": "http://uniquelidkc3s2dussvwp473o6dtcaireq2ivgbfts6oh3n7427ojlad.onion/?q={}",
    "venusosej": "http://venusosejno7oie4c73vsvrdw5k5gyhrhmq3apovwvy3qihub2dfppad.onion/?q={}",
    "venusoswt": "http://venusoswti4gxjlxplnx66syjiv4veexixh7qkbjbmgf7nmctagqvwqd.onion/?q={}",
    "yahooirqy": "http://yahooirqyxszdwot6gdkp237lj4nlw3jdlim2kl5cwj6wgosonqzunqd.onion/?q={}",
    "zoozle4q": "http://zoozle4qpbnectvv3ndvcalisaka65kven4xiomvs55otfnuaxewa2yd.onion/?q={}",
    
    # Additional search engines with alternative patterns
    "duckduckgo": "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/?t=h_&q={}&ia=web",
    "notevil": "http://notevilmtxf25uw7tskqxj6njlpebyrmlrerfv5hc4tuq7c7hilbyiqd.onion/?q={}",
    "onionland": "http://3bbad7fauom4d6sgppalyqddsqbf5u5p56b5k5uk2zxsy3d6ey2jobad.onion/?q={}",
    "haystak": "http://haystak5njsmn2hqkewecpaxetahtwhsbsa64jom2k22z5afxhnpxfid.onion/?q={}",
    "metagerv": "http://metagerv65pwclop2rsfzg4jwowpavpwd6grhhlvdgsswvo6ii4akgyd.onion/search?q={}",
    "narcoo": "http://narcooqom5mfevbeb6gck5tg5y2g2f5grywcu7cp4b3bvsmlvph66wqd.onion/search?q={}",
    "on62jjk": "http://on62jjkocppf3alrznspngqt4v7emcyxcxz4r5cq5pwnajyshr2u4uqd.onion/search?q={}",
    "tor66": "http://tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxiuh34iid.onion/search?q={}",
    "iy3544": "http://iy3544gmoeclh5de6gez2256v6pjh4omhpqdh2wpeeppjtvqmjhkfwad.onion/search?q={}",
    "uquroy": "http://uquroyobsaquslaunwkz6bmc3wutpzvwe7mv62xeq64645a57bugnsyd.onion/search?q={}",
    "tordex": "http://tordexyb63aknnvuzyqabeqx6l7zdiesfos22nisv6zbj6c6o3h6ijyd.onion/?query={}",
    
    # Additional search engines with various patterns
    "onionsearch": "http://kn3hl4xwon63tc6hpjrwza2npb7d4w5yhbzq7jjewpfzyhsd65tm6dad.onion/?q={}",
    "searx": "http://searxingux6na3djgdrcfwutafxmmagerhbieihsgu7sgmjee3u777yd.onion/?q={}",
    "devilsearch1": "http://search65pq2x5oh4o4qlxk2zvoa5zhbfi6mx4br4oc33rpxuayauwsqd.onion/?q={}",
    "devilsearch2": "http://freewzvfroedixqklf6iqpwckoxsqah57qoqzfhrw6kaw2hjjbcf42id.onion/?q={}",
    "devilsearch3": "http://searchbzgixuy524pl2wcsy4ozl5vzh4mjibbuft5f5irajlz5vw5jad.onion/?q={}",
    "digdeep1": "http://digdeep4orxw6psc33yxa2dgmuycj74zi6334xhxjlgppw6odvkzkiad.onion/?q={}",
    "digdeep2": "http://uvgbd5mgizntrfghf2c77e2gp3ps3tzonmizfs4uva6cbeuxhkszedid.onion/?q={}",
    "digdeep3": "http://us63bgjkxwpyrpvsqom6kw3jcy2yujbplkhtzt64yykt42ne2ms7p4yd.onion/?q={}",
    "digdeep4": "http://mijpbiurmidlyzn4n54qfsmkrsgoggbgrwarcwn2sd3x6mrqqf7qleid.onion/?q={}"
}

# Alternative search patterns in case the above don't work
ALTERNATIVE_SEARCH_PATTERNS = {
    #"haystak": "http://haystak5njsmn2hqkewecpaxetahtwhsbsa64jom2k22z5afxhnpxfid.onion/search?q={}",
    #"metagerv": "http://metagerv65pwclop2rsfzg4jwowpavpwd6grhhlvdgsswvo6ii4akgyd.onion/?q={}",
    #"narcoo": "http://narcooqom5mfevbeb6gck5tg5y2g2f5grywcu7cp4b3bvsmlvph66wqd.onion/?q={}",
    #"on62jjk": "http://on62jjkocppf3alrznspngqt4v7emcyxcxz4r5cq5pwnajyshr2u4uqd.onion/?q={}",
    #"tor66": "http://tor66sewebgixwhcqfnp5inzp5x5uohhdy3kvtnyfxc2e5mxiuh34iid.onion/search?q={}",
    #"iy3544": "http://iy3544gmoeclh5de6gez2256v6pjh4omhpqdh2wpeeppjtvqmjhkfwad.onion/search?q={}",
    #"uquroy": "http://uquroyobsaquslaunwkz6bmc3wutpzvwe7mv62xeq64645a57bugnsyd.onion/search?q={}",
    
    # Alternative patterns for new search engines
    #"duckduckgo": "https://duckduckgogg42xjoc72x3sjasowoarfbgcmvfimaftt6twagswzczad.onion/search?q={}",
    #"notevil": "http://notevilmtxf25uw7tskqxj6njlpebyrmlrerfv5hc4tuq7c7hilbyiqd.onion/search?q={}",
    #"onionland": "http://3bbad7fauom4d6sgppalyqddsqbf5u5p56b5k5uk2zxsy3d6ey2jobad.onion/search?q={}",
    #"onionsearch": "http://kn3hl4xwon63tc6hpjrwza2npb7d4w5yhbzq7jjewpfzyhsd65tm6dad.onion/search?q={}",
    #"searx": "http://searxingux6na3djgdrcfwutafxmmagerhbieihsgu7sgmjee3u777yd.onion/search?q={}",
    #"torch": "http://torchdeedp3i2jigzjdmfpn5ttjhthh5wbmda2rr3jvqjg5p77c54dqd.onion/search?q={}"
}

OUTPUT_FILE = f"discovered_onions_{datetime.utcnow().strftime('%Y%m%d')}.csv"
ADDRESSES_FILE = f"crypto_addresses_{datetime.utcnow().strftime('%Y%m%d')}.csv"
KEYWORDS = [
    # Core CSAM terms
    'loli', 'boys', 'girls', 'sex', 'sexy', 'rape', 'lolita', 'loliporn',
    'cp', 'cp video', 'child porn', 'child xxx', 'preteen', 'child', 'red room', 'teen', 'cute boys',
    'childxxx', 'preteen', 'child', 'csam', 'csam viewer', 'csam access', 'watch child porn', 'view child porn', 'csam gallery',
    
    # Additional CSAM-specific terms
    'pedo', 'pedophile', 'pedophilia', 'ephebophile', 'hebephile', 'map', 'minor attracted person',
    'boylove', 'girllove', 'bl', 'gl', 'boy lover', 'girl lover', 'boylover', 'girllover',
    'young teen', 'very young', 'tiny teen', 'little girl', 'little boy', 'baby girl', 'baby boy',
    'infant', 'toddler', 'preschool', 'kindergarten', 'elementary', 'middle school', 'high school',
    'school girl', 'school boy', 'uniform', 'sailor', 'nurse', 'maid', 'angel', 'innocent',
    'virgin', 'first time', 'deflower', 'defloration', 'pure', 'clean', 'fresh', 'new',
    'underage', 'minor', 'juvenile', 'youth', 'adolescent', 'pubescent', 'prepubescent',
    
# Trafficking and exploitation terms
    'child exploitation', 'minor exploitation', 'youth exploitation', 'teen exploitation', 
    'girl exploitation', 'boy exploitation', 'child prostitution', 'teen prostitution', 
    'minor prostitution', 'forced prostitution', 'coerced prostitution', 'child trafficking',
    'sex trafficking', 'human trafficking', 'trafficked person', 'trafficked girl', 
    'trafficked boy', 'trafficked child', 'trafficked teen', 'trafficked minor',
    'victim of trafficking', 'trafficking victim', 'exploitation victim', 'abuse victim',
    'sexual abuse', 'child abuse', 'teen abuse', 'minor abuse', 'youth abuse',
    'commercial sexual exploitation', 'csec', 'commercial sex', 'sex work', 'prostitution',
    
  # Additional search terms
    'child model', 'teen model', 'young model', 'child actress', 'teen actress',
    'child star', 'teen star', 'child celebrity', 'teen celebrity', 'child influencer',
    'teen influencer', 'child content', 'teen content', 'young content', 'minor content',
    'child photo', 'teen photo', 'young photo', 'child video', 'teen video', 'young video',
    'child pic', 'teen pic', 'young pic', 'child clip', 'teen clip', 'young clip',
    'child movie', 'teen movie', 'young movie', 'child film', 'teen film', 'young film',
    
    # Forum and community terms
    'child forum', 'teen forum', 'loli forum', 'minor forum', 'child board', 'teen board',
    'loli board', 'minor board', 'child community', 'teen community', 'loli community',
    'child chat', 'teen chat', 'loli chat', 'minor chat', 'child room', 'teen room',
    'loli room', 'minor room', 'child group', 'teen group', 'loli group', 'minor group',
    
    # Market and shop terms
    'child market', 'teen market', 'loli market', 'minor market', 'child shop', 'teen shop',
    'loli shop', 'minor shop', 'child store', 'teen store', 'loli store', 'minor store',
    'child vendor', 'teen vendor', 'loli vendor', 'minor vendor', 'child seller', 'teen seller',
    'loli seller', 'minor seller', 'child trader', 'teen trader', 'loli trader', 'minor trader',
    
    # Action and access terms
    'watch child', 'view child', 'download child', 'stream child', 'watch teen', 'view teen',
    'download teen', 'stream teen', 'watch loli', 'view loli', 'download loli', 'stream loli',
    'access child', 'access teen', 'access loli', 'access minor', 'get child', 'get teen',
    'get loli', 'get minor', 'find child', 'find teen', 'find loli', 'find minor',
    'buy child', 'buy teen', 'buy loli', 'buy minor', 'sell child', 'sell teen', 'sell loli',
    'sell minor', 'trade child', 'trade teen', 'trade loli', 'trade minor',
    
]

# Cryptocurrency address patterns
CRYPTO_PATTERNS = {
    "BTC": re.compile(r"\b(bc1[a-zA-Z0-9]{25,90}|[13][a-zA-HJ-NP-Z0-9]{25,39})\b"),
    "ETH": re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
    "XMR": re.compile(r"\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b"),
    "TRON": re.compile(r"\bT[1-9A-HJ-NP-Za-km-z]{33}\b"),
    "SOL": re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{44}\b")
}

MAX_DEPTH = 3
SLEEP_BETWEEN_REQUESTS = (2, 8)
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
ROTATE_EVERY_N = 25
MAX_WORKERS = 10

# List of known link directory URLs (broad phase)
LINK_DIRECTORY_URLS = [
    # Add some of the SEED_URLS as directory URLs for broad discovery
    "http://on62jjkocppf3alrznspngqt4v7emcyxcxz4r5cq5pwnajyshr2u4uqd.onion",
    "http://4yr6xac6fvhi6mdwm6julwnvkrj5whw43l7txyv267dm37stsn7i3rid.onion",
    "http://ahmiai45jeruhemta4pg344x3btevkhadp64f6zppk32nhxays6bw6ad.onion",
    "http://qg24mbrij6rzxr77eovjwjzw7zwn7brmegr3yvwvppj4vhdxeuezkdqd.onion",
    "http://searches7gwtdwrzrpczfosri3dwihqxvkacqfcxc5r6ku72ehra7bqd.onion",
    "http://iy3544gmoeclh5de6gez2256v6pjh4omhpqdh2wpeeppjtvqmjhkfwad.onion",
    "http://torchac4h5bchwcxnnl566u5uuaclrufmaecv7ll2n64aggzsy5of2yd.onion",
    "http://metagerv65pwclop2rsfzg4jwowpavpwd6grhhlvdgsswvo6ii4akgyd.onion",
    "http://tornadox5n4g7apkcr23yqyi66eltomazrfgkljy22ccajywd2jsihid.onion",
    "http://publica6d3mkbqevzg6rdftngrzczxueaxgmrdqzkoxyfwpmlw6elfqd.onion"
]

# ----------------------------
# Setup Requests via Tor
# ----------------------------
session = requests.Session()
session.proxies = {
    "http": TOR_SOCKS_PROXY,
    "https": TOR_SOCKS_PROXY
}
session.headers.update({"User-Agent": USER_AGENT})

# Thread-safe data structures
seen_lock = threading.Lock()
discovered_lock = threading.Lock()
file_lock = threading.Lock()
page_counter_lock = threading.Lock()
progress_lock = threading.Lock()
seen = set()
discovered = set()
page_counter = 0
addresses_found = 0
last_processed_url = None
max_depth_urls = set()  # Track URLs at maximum depth for deeper crawling

# ----------------------------
# Progress Tracking Functions
# ----------------------------
def extract_crypto_addresses(html_content):
    """Extract cryptocurrency addresses from HTML content"""
    addresses = []
    text = html_content.lower()
    
    for chain, pattern in CRYPTO_PATTERNS.items():
        matches = pattern.findall(html_content)
        for match in matches:
            # Basic validation
            if len(match) > 10 and not match.isdigit():
                addresses.append(f"{chain}:{match}")
    
    return addresses

def save_progress(queue, seen_urls, discovered_urls, current_depth=0):
    """Save current progress to allow restart"""
    progress_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'queue': queue,
        'seen_urls': list(seen_urls),
        'discovered_urls': list(discovered_urls),
        'max_depth_urls': list(max_depth_urls),
        'page_counter': page_counter,
        'addresses_found': addresses_found,
        'last_processed_url': last_processed_url,
        'current_depth': current_depth,
        'seed_urls': SEED_URLS
    }
    
    with progress_lock:
        try:
            with open(PROGRESS_FILE, 'w') as f:
                json.dump(progress_data, f, indent=2)
            logger.info(f"💾 Progress saved: {len(queue)} URLs in queue, {len(seen_urls)} seen, {len(discovered_urls)} discovered, {addresses_found} addresses found, {len(max_depth_urls)} max depth URLs")
        except Exception as e:
            logger.error(f"❌ Failed to save progress: {e}")

def load_progress():
    """Load progress from previous run"""
    if not os.path.exists(PROGRESS_FILE):
        logger.info("🆕 No previous progress found, starting fresh")
        return None, set(), set(), 0, 0, None, set()
    
    try:
        with open(PROGRESS_FILE, 'r') as f:
            progress_data = json.load(f)
        
        logger.info(f"🔄 Loading progress from {progress_data['timestamp']}")
        logger.info(f"📊 Previous run: {len(progress_data['queue'])} URLs in queue, {len(progress_data['seen_urls'])} seen, {len(progress_data['discovered_urls'])} discovered, {progress_data.get('addresses_found', 0)} addresses found, {len(progress_data.get('max_depth_urls', []))} max depth URLs")
        
        return (
            progress_data['queue'],
            set(progress_data['seen_urls']),
            set(progress_data['discovered_urls']),
            progress_data.get('page_counter', 0),
            progress_data.get('addresses_found', 0),
            progress_data.get('last_processed_url', None),
            set(progress_data.get('max_depth_urls', []))
        )
    except Exception as e:
        logger.error(f"❌ Failed to load progress: {e}")
        return None, set(), set(), 0, 0, None, set()

def save_restart_info(url, depth, error=None):
    """Save information about where the crawler crashed"""
    restart_data = {
        'timestamp': datetime.utcnow().isoformat(),
        'last_url': url,
        'last_depth': depth,
        'error': str(error) if error else None,
        'seed_urls': SEED_URLS
    }
    
    try:
        with open(RESTART_FILE, 'w') as f:
            json.dump(restart_data, f, indent=2)
        logger.info(f"💾 Restart info saved for URL: {url}")
    except Exception as e:
        logger.error(f"❌ Failed to save restart info: {e}")

def load_restart_info():
    """Load restart information"""
    if not os.path.exists(RESTART_FILE):
        return None
    
    try:
        with open(RESTART_FILE, 'r') as f:
            restart_data = json.load(f)
        logger.info(f"🔄 Found restart info from {restart_data['timestamp']}")
        logger.info(f"📍 Last URL: {restart_data['last_url']} (depth: {restart_data['last_depth']})")
        if restart_data.get('error'):
            logger.warning(f"⚠️  Previous error: {restart_data['error']}")
        return restart_data
    except Exception as e:
        logger.error(f"❌ Failed to load restart info: {e}")
        return None

# ----------------------------
# Functions
# ----------------------------
def load_previously_discovered():
    """Scans for previous output files and loads successfully crawled URLs to avoid re-crawling."""
    previously_discovered = set()
    
    # Find all previous discovery files
    previous_files = glob.glob("discovered_onions_*.csv")
    if not previous_files:
        logger.info("No previous discovery files found.")
        return previously_discovered

    logger.info(f"Found {len(previous_files)} previous discovery files. Loading successfully crawled URLs to skip...")
    
    for f_name in previous_files:
        try:
            with open(f_name, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)  # Skip header
                
                # Find the relevant columns
                try:
                    url_index = header.index('onion_url')
                    source_index = header.index('source')
                    depth_index = header.index('depth')
                except ValueError:
                    # If we can't find the expected columns, skip this file
                    logger.warning(f"⚠️  Skipping {f_name} - missing expected columns")
                    continue
                
                for row in reader:
                    if len(row) > max(url_index, source_index, depth_index):
                        full_url = row[url_index]
                        source_url = row[source_index]
                        depth = int(row[depth_index]) if row[depth_index].isdigit() else 0
                        
                        # Only consider URLs that were actually crawled (not just discovered)
                        # Skip URLs that were discovered from search engines or at depth 0 (seed URLs)
                        if depth > 0 and not any(engine in source_url for engine in ['duckduckgo', 'notevil', 'onionland', 'torch', 'search']):
                            parsed_url = urlparse(full_url)
                            if parsed_url.hostname:
                               clean_onion = extract_clean_onion(parsed_url.hostname)
                               if clean_onion:
                                   previously_discovered.add(clean_onion)
        except Exception as e:
            logger.error(f"⚠️  Could not read or process {f_name}: {e}")
    
    logger.info(f"✅ Loaded {len(previously_discovered)} previously successfully crawled URLs (excluding seed URLs and search discoveries).")
    return previously_discovered

def rotate_tor_identity():
    try:
        with socket.create_connection(("127.0.0.1", TOR_CONTROL_PORT), timeout=CONTROL_TIMEOUT) as s:
            s.sendall(f'AUTHENTICATE "{TOR_CONTROL_PASSWORD}"\r\n'.encode())
            if b'250' not in s.recv(1024):
                logger.error("❌ Tor auth failed.")
                return False
            s.sendall(b'SIGNAL NEWNYM\r\n')
            s.recv(1024)
            logger.info("🔄 Tor identity rotated.")
            return True
    except Exception as e:
        logger.error(f"❌ Tor control error: {e}")
        return False

def extract_clean_onion(domain):
    # More flexible onion address matching
    # Try the strict 56-character format first
    match = re.search(r"([a-z2-7]{56})\.onion", domain)
    if match:
        return match.group(0)
    
    # Try shorter onion addresses (some are 16 characters)
    match = re.search(r"([a-z2-7]{16})\.onion", domain)
    if match:
        return match.group(0)
    
    # Try any onion address format
    match = re.search(r"([a-z2-7]{10,56})\.onion", domain)
    if match:
        return match.group(0)
    
    return None

def extract_onion_links(html, base_url):
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    all_onion_urls = []  # Track all onion URLs found
    
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a['href'])
        parsed = urlparse(href)
        if parsed.hostname and ".onion" in parsed.hostname:
            all_onion_urls.append(parsed.hostname)  # Track all onion domains
            clean = extract_clean_onion(parsed.hostname)
            if clean:
                links.add(clean)
    
    # Show what we found
    if all_onion_urls:
        logger.info(f"🔍 Found {len(all_onion_urls)} onion URLs in HTML: {all_onion_urls[:5]}...")  # Show first 5
        logger.info(f"🔍 After filtering: {len(links)} clean onion addresses: {list(links)}")
    else:
        logger.info(f"🔍 No onion URLs found in HTML")
    
    return links

def extract_title(html):
    soup = BeautifulSoup(html, "html.parser")
    title_tag = soup.find("title")
    return title_tag.text.strip() if title_tag else ""

def detect_search_forms(html, base_url):
    """Detect search forms on a page and return search patterns"""
    soup = BeautifulSoup(html, "html.parser")
    search_patterns = []
    
    # Look for search forms
    forms = soup.find_all("form")
    for form in forms:
        # Check if form has search-related attributes or inputs
        form_action = form.get("action", "")
        form_method = form.get("method", "get").lower()
        
        # Look for search input fields
        search_inputs = form.find_all("input", type=["text", "search"])
        if not search_inputs:
            continue
            
        # Check if form looks like a search form
        form_text = form.get_text().lower()
        search_indicators = ["search", "q", "query", "keywords", "find"]
        is_search_form = any(indicator in form_text for indicator in search_indicators)
        
        if is_search_form or any("search" in inp.get("name", "").lower() or "q" in inp.get("name", "").lower() for inp in search_inputs):
            # Determine search URL pattern
            if form_action:
                if form_action.startswith("http"):
                    search_url = form_action
                else:
                    search_url = urljoin(base_url, form_action)
            else:
                search_url = base_url
                
            # Get the search parameter name (usually 'q' or 'search')
            search_param = "q"  # default
            for inp in search_inputs:
                name = inp.get("name", "")
                if name in ["q", "search", "query", "keywords"]:
                    search_param = name
                    break
            
            # Create search pattern
            if form_method == "get":
                if "?" in search_url:
                    search_pattern = f"{search_url}&{search_param}={{}}"
                else:
                    search_pattern = f"{search_url}?{search_param}={{}}"
            else:
                # For POST forms, we'll use GET pattern as fallback
                if "?" in search_url:
                    search_pattern = f"{search_url}&{search_param}={{}}"
                else:
                    search_pattern = f"{search_url}?{search_param}={{}}"
            
            search_patterns.append({
                "url": search_url,
                "pattern": search_pattern,
                "method": form_method,
                "param": search_param
            })
            logger.info(f"🔍 Detected search form: {search_pattern}")
    
    return search_patterns

def search_on_discovered_engine(search_pattern, keyword, engine_url, depth):
    """Search for a keyword on a discovered search engine"""
    try:
        # Create search URL
        search_url = search_pattern["pattern"].format(requests.utils.quote(keyword))
        logger.info(f"🔍 Dynamic search: '{keyword}' on {engine_url} -> {search_url}")
        
        # Make search request
        thread_session = requests.Session()
        thread_session.proxies = {
            "http": TOR_SOCKS_PROXY,
            "https": TOR_SOCKS_PROXY
        }
        thread_session.headers.update({"User-Agent": USER_AGENT})
        
        resp = thread_session.get(search_url, timeout=15)
        if resp.status_code == 200:
            # Extract onion links from search results
            search_links = extract_onion_links(resp.text, search_url)
            logger.info(f"🔍 Dynamic search found {len(search_links)} links for '{keyword}' on {engine_url}")
            return search_links
        else:
            logger.debug(f"🔍 Dynamic search failed with status {resp.status_code} for {search_url}")
            return set()
            
    except Exception as e:
        logger.debug(f"🔍 Dynamic search error for {engine_url}: {e}")
        return set()

def perform_dynamic_searches(html, base_url, depth):
    """Perform intelligent dynamic searches when search forms are detected on a page"""
    discovered_links = set()
    
    # Detect search forms
    search_patterns = detect_search_forms(html, base_url)
    if not search_patterns:
        return discovered_links
    
    logger.info(f"🔍 Found {len(search_patterns)} search forms on {base_url}")
    
    # Use smart queries instead of just first 5 keywords
    smart_queries = generate_smart_search_queries()
    
    # Prioritize queries based on the page content
    page_title = extract_title(html).lower()
    page_text = BeautifulSoup(html, "html.parser").get_text().lower()
    
    # Score queries based on relevance to current page
    scored_queries = []
    for query in smart_queries[:20]:  # Use top 20 smart queries
        score = 0
        query_words = query.lower().split()
        
        # Check if query words appear in page title or content
        for word in query_words:
            if word in page_title:
                score += 3  # High weight for title matches
            if word in page_text:
                score += 1  # Lower weight for content matches
        
        scored_queries.append((query, score))
    
    # Sort by relevance score and take top queries
    scored_queries.sort(key=lambda x: x[1], reverse=True)
    prioritized_queries = [query for query, score in scored_queries[:10]]  # Use top 10 most relevant
    
    logger.info(f"🧠 Using {len(prioritized_queries)} prioritized queries for dynamic search on {base_url}")
    
    for search_pattern in search_patterns:
        for query in prioritized_queries:
            try:
                # Search on this discovered engine
                links = search_on_discovered_engine(search_pattern, query, base_url, depth)
                discovered_links.update(links)
                
                # Small delay between searches
                time.sleep(random.randint(1, 3))
                
            except Exception as e:
                logger.debug(f"🔍 Error in dynamic search: {e}")
                continue
    
    logger.info(f"🔍 Dynamic searches on {base_url} discovered {len(discovered_links)} new links")
    return discovered_links

def generate_smart_search_queries():
    """Generate intelligent search queries using combinations and variations"""
    smart_queries = []
    
    # Primary high-value keywords (CSAM specific)
    primary_keywords = ['cp', 'loli', 'child', 'teen', 'minor', 'preteen', 'lolita', 'pedo', 'map']
    
    # Secondary descriptive keywords
    secondary_keywords = ['porn', 'video', 'gallery', 'access', 'view', 'watch', 'download', 'stream']
    
    # Tertiary action/context keywords
    tertiary_keywords = ['site', 'forum', 'board', 'market', 'shop', 'store', 'service', 'provider']
    
    # Law Enforcement - Trafficking specific terms
    trafficking_terms = ['john', 'trick', 'date', 'client', 'pimp', 'madam', 'stable', 'stroll', 'track']
    
    # Law Enforcement - Code words
    code_words = ['fresh meat', 'fresh fish', 'new meat', 'new fish', 'fresh catch', 'baby doll', 'kitten', 'puppy']
    
    # Law Enforcement - Service terms
    service_terms = ['massage', 'spa', 'parlor', 'salon', 'studio', 'clinic', 'center', 'outcall', 'incall']
    
    # Law Enforcement - Financial terms
    financial_terms = ['donation', 'tip', 'fee', 'rate', 'charge', 'cost', 'price', 'hourly']
    
    # 1. Single primary keywords (high precision)
    smart_queries.extend(primary_keywords)
    
    # 2. Primary + Secondary combinations (medium precision, high recall)
    for primary in primary_keywords:
        for secondary in secondary_keywords:
            smart_queries.append(f"{primary} {secondary}")
    
    # 3. Primary + Tertiary combinations (discovery focused)
    for primary in primary_keywords:
        for tertiary in tertiary_keywords:
            smart_queries.append(f"{primary} {tertiary}")
    
    # 4. Law Enforcement - Trafficking combinations
    for trafficking in trafficking_terms:
        for primary in primary_keywords:
            smart_queries.append(f"{trafficking} {primary}")
            smart_queries.append(f"{primary} {trafficking}")
    
    # 5. Law Enforcement - Code word combinations
    for code in code_words:
        smart_queries.append(code)
        for primary in primary_keywords:
            smart_queries.append(f"{code} {primary}")
            smart_queries.append(f"{primary} {code}")
    
    # 6. Law Enforcement - Service combinations
    for service in service_terms:
        for primary in primary_keywords:
            smart_queries.append(f"{service} {primary}")
            smart_queries.append(f"{primary} {service}")
    
    # 7. Law Enforcement - Financial combinations
    for financial in financial_terms:
        for primary in primary_keywords:
            smart_queries.append(f"{financial} {primary}")
            smart_queries.append(f"{primary} {financial}")
    
    # 8. Multi-word primary combinations
    smart_queries.extend([
        'child porn', 'child video', 'teen porn', 'minor porn', 'preteen porn',
        'loli porn', 'lolita porn', 'child gallery', 'teen gallery', 'minor gallery',
        'pedo porn', 'map porn', 'pedophile porn', 'minor attracted person'
    ])
    
    # 9. Action-oriented queries
    smart_queries.extend([
        'watch child', 'view child', 'download child', 'stream child',
        'watch teen', 'view teen', 'download teen', 'stream teen',
        'watch loli', 'view loli', 'download loli', 'stream loli',
        'access child', 'access teen', 'access loli', 'access minor'
    ])
    
    # 10. Forum/community focused queries
    smart_queries.extend([
        'child forum', 'teen forum', 'loli forum', 'minor forum',
        'child board', 'teen board', 'loli board', 'minor board',
        'child community', 'teen community', 'loli community',
        'pedo forum', 'map forum', 'pedophile forum', 'minor attracted person forum'
    ])
    
    # 11. Market/shop focused queries
    smart_queries.extend([
        'child market', 'teen market', 'loli market', 'minor market',
        'child shop', 'teen shop', 'loli shop', 'minor shop',
        'child store', 'teen store', 'loli store', 'minor store',
        'pedo market', 'map market', 'pedophile market', 'minor attracted person market'
    ])
    
    # 12. Law Enforcement - Specific trafficking queries
    smart_queries.extend([
        'john child', 'trick child', 'date child', 'client child',
        'pimp child', 'madam child', 'stable child', 'stroll child',
        'john teen', 'trick teen', 'date teen', 'client teen',
        'pimp teen', 'madam teen', 'stable teen', 'stroll teen',
        'john loli', 'trick loli', 'date loli', 'client loli',
        'pimp loli', 'madam loli', 'stable loli', 'stroll loli'
    ])
    
    # 13. Law Enforcement - Service specific queries
    smart_queries.extend([
        'massage child', 'spa child', 'parlor child', 'salon child',
        'studio child', 'clinic child', 'center child', 'outcall child',
        'massage teen', 'spa teen', 'parlor teen', 'salon teen',
        'studio teen', 'clinic teen', 'center teen', 'outcall teen',
        'massage loli', 'spa loli', 'parlor loli', 'salon loli',
        'studio loli', 'clinic loli', 'center loli', 'outcall loli'
    ])
    
    # 14. Law Enforcement - Financial specific queries
    smart_queries.extend([
        'donation child', 'tip child', 'fee child', 'rate child',
        'charge child', 'cost child', 'price child', 'hourly child',
        'donation teen', 'tip teen', 'fee teen', 'rate teen',
        'charge teen', 'cost teen', 'price teen', 'hourly teen',
        'donation loli', 'tip loli', 'fee loli', 'rate loli',
        'charge loli', 'cost loli', 'price loli', 'hourly loli'
    ])
    
    # 15. Law Enforcement - Backpage/Craigslist replacement queries
    smart_queries.extend([
        'backpage child', 'backpage teen', 'backpage loli', 'backpage minor',
        'craigslist child', 'craigslist teen', 'craigslist loli', 'craigslist minor',
        'classified child', 'classified teen', 'classified loli', 'classified minor',
        'backpage replacement', 'craigslist replacement', 'classified ads'
    ])
    
    # Remove duplicates and limit to reasonable number
    unique_queries = list(set(smart_queries))
    return unique_queries[:100]  # Increased limit to 100 for better coverage

def analyze_search_results(html_content, search_url):
    """Analyze search results to extract useful information for further searches"""
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Extract page titles and snippets
    titles = []
    snippets = []
    
    # Look for common search result patterns
    title_selectors = ['h1', 'h2', 'h3', '.title', '.result-title', '.search-title']
    snippet_selectors = ['.snippet', '.description', '.result-description', '.summary']
    
    for selector in title_selectors:
        elements = soup.select(selector)
        titles.extend([elem.get_text().strip() for elem in elements if elem.get_text().strip()])
    
    for selector in snippet_selectors:
        elements = soup.select(selector)
        snippets.extend([elem.get_text().strip() for elem in elements if elem.get_text().strip()])
    
    # Extract potential new keywords from titles and snippets
    all_text = ' '.join(titles + snippets).lower()
    
    # Find words that appear frequently and might be relevant
    words = re.findall(r'\b[a-z]{3,}\b', all_text)
    word_freq = {}
    for word in words:
        if word not in ['the', 'and', 'for', 'with', 'this', 'that', 'have', 'from', 'they', 'will', 'been', 'were', 'said', 'each', 'which', 'their', 'time', 'would', 'there', 'could', 'other', 'than', 'first', 'very', 'after', 'most', 'what', 'over', 'think', 'also', 'when', 'some', 'into', 'just', 'only', 'know', 'take', 'than', 'them', 'well', 'even', 'back', 'here', 'make', 'life', 'both', 'between', 'never', 'under', 'last', 'should', 'work', 'may', 'through', 'call', 'world', 'over', 'school', 'still', 'try', 'hand', 'again', 'place', 'around', 'both', 'group', 'often', 'run', 'important', 'until', 'children', 'side', 'feet', 'car', 'mile', 'night', 'walk', 'white', 'sea', 'began', 'grow', 'took', 'river', 'four', 'carry', 'state', 'once', 'book', 'hear', 'stop', 'without', 'second', 'later', 'miss', 'idea', 'enough', 'eat', 'face', 'watch', 'far', 'Indian', 'real', 'almost', 'let', 'above', 'girl', 'sometimes', 'mountain', 'cut', 'young', 'talk', 'soon', 'list', 'song', 'being', 'leave', 'family', 'it\'s']:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Return top relevant words
    relevant_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
    return [word for word, freq in relevant_words if freq >= 2]

def search_keywords_on_engines():
    """Smart search using intelligent query generation and result analysis"""
    discovered_from_search = set()
    smart_queries = generate_smart_search_queries()
    total_searches = len(SEARCH_ENGINE_PATTERNS) * len(smart_queries)
    completed_searches = 0
    
    logger.info(f"🧠 Starting SMART keyword search on {len(SEARCH_ENGINE_PATTERNS)} search engines")
    logger.info(f"🧠 Using {len(smart_queries)} intelligent queries (vs {len(KEYWORDS)} basic keywords)")
    logger.info(f"🧠 Total searches to perform: {total_searches}")
    
    # Track discovered keywords for adaptive searching
    discovered_keywords = set()
    
    for engine_name, search_url_pattern in SEARCH_ENGINE_PATTERNS.items():
        logger.info(f"🔍 Searching on {engine_name} with smart queries...")
        
        for query in smart_queries:
            try:
                # Try primary search pattern first
                search_url = search_url_pattern.format(requests.utils.quote(query))
                logger.info(f"🧠 Smart search: '{query}' on {engine_name}")
                logger.info(f"🔍 DEBUG: Search URL: {search_url}")
                
                # Make search request
                thread_session = requests.Session()
                thread_session.proxies = {
                    "http": TOR_SOCKS_PROXY,
                    "https": TOR_SOCKS_PROXY
                }
                thread_session.headers.update({"User-Agent": USER_AGENT})
                
                resp = thread_session.get(search_url, timeout=15)
                logger.info(f"🔍 Search response status: {resp.status_code}")
                
                # If primary pattern failed, try alternative pattern
                if resp.status_code != 200 and engine_name in ALTERNATIVE_SEARCH_PATTERNS:
                    alternative_url = ALTERNATIVE_SEARCH_PATTERNS[engine_name].format(requests.utils.quote(query))
                    logger.info(f"🔍 Trying alternative pattern for {engine_name}")
                    logger.info(f"🔍 DEBUG: Alternative URL: {alternative_url}")
                    resp = thread_session.get(alternative_url, timeout=15)
                    logger.info(f"🔍 Alternative search response status: {resp.status_code}")
                
                if resp.status_code == 200:
                    # DEBUG: Check if we're getting actual search results or a block page
                    page_title = extract_title(resp.text)
                    logger.info(f"🔍 DEBUG: Search result page title: '{page_title}'")
                    
                    # Check if we got blocked or got a generic page
                    if "duckduckgo" in page_title.lower() and len(resp.text) < 5000:
                        logger.warning(f"⚠️ DEBUG: Possible block page detected - small response size ({len(resp.text)} chars)")
                    
                    # Extract onion links from search results
                    search_links = extract_onion_links(resp.text, search_url)
                    logger.info(f"🔍 Found {len(search_links)} onion links for query '{query}' on {engine_name}")
                    
                    # DEBUG: Show what links were actually found
                    if search_links:
                        logger.info(f"🔍 DEBUG: Links found: {list(search_links)}")
                    else:
                        logger.info(f"🔍 DEBUG: No links found in search results")
                    
                    # Analyze search results for new keywords
                    new_keywords = analyze_search_results(resp.text, search_url)
                    discovered_keywords.update(new_keywords)
                    logger.info(f"🧠 Discovered {len(new_keywords)} new keywords from search results")
                    
                    # Add discovered links and save them immediately to CSV
                    for link in search_links:
                        if link not in discovered_from_search:
                            discovered_from_search.add(link)
                            logger.info(f"➕ Discovered from smart search: {link} (query: {query}, engine: {engine_name})")
                            
                            # Save to CSV file immediately
                            with discovered_lock:
                                if link not in discovered:
                                    discovered.add(link)
                                    row = [f"http://{link}", search_url, 0, datetime.utcnow().isoformat(), f"Found via smart search: {query}"]
                                    with file_lock:
                                        with open(OUTPUT_FILE, "a", newline='') as f:
                                            writer = csv.writer(f)
                                            writer.writerow(row)
                
                # Update progress
                completed_searches += 1
                progress_percent = (completed_searches / total_searches) * 100
                logger.info(f"📊 Smart search progress: {completed_searches}/{total_searches} ({progress_percent:.1f}%) - Found {len(discovered_from_search)} unique URLs, {len(discovered_keywords)} new keywords")
                
                # Sleep between searches to be respectful
                sleep_time = random.randint(*SLEEP_BETWEEN_REQUESTS)
                time.sleep(sleep_time)
                
                # Rotate Tor identity periodically
                global page_counter
                page_counter += 1
                if page_counter % ROTATE_EVERY_N == 0:
                    rotate_tor_identity()
                    
            except Exception as e:
                logger.error(f"❌ Error in smart search '{query}' on {engine_name}: {e}")
                completed_searches += 1
                continue
        
        # After completing each engine, do adaptive searches with discovered keywords
        if discovered_keywords:
            logger.info(f"🧠 Performing adaptive searches on {engine_name} with {len(discovered_keywords)} discovered keywords")
            adaptive_queries = list(discovered_keywords)[:10]  # Use top 10 discovered keywords
            
            for adaptive_query in adaptive_queries:
                try:
                    search_url = search_url_pattern.format(requests.utils.quote(adaptive_query))
                    logger.info(f"🧠 Adaptive search: '{adaptive_query}' on {engine_name}")
                    
                    thread_session = requests.Session()
                    thread_session.proxies = {
                        "http": TOR_SOCKS_PROXY,
                        "https": TOR_SOCKS_PROXY
                    }
                    thread_session.headers.update({"User-Agent": USER_AGENT})
                    
                    resp = thread_session.get(search_url, timeout=15)
                    if resp.status_code == 200:
                        search_links = extract_onion_links(resp.text, search_url)
                        logger.info(f"🔍 Adaptive search found {len(search_links)} links for '{adaptive_query}'")
                        
                        for link in search_links:
                            if link not in discovered_from_search:
                                discovered_from_search.add(link)
                                logger.info(f"➕ Discovered from adaptive search: {link}")
                                
                                with discovered_lock:
                                    if link not in discovered:
                                        discovered.add(link)
                                        row = [f"http://{link}", search_url, 0, datetime.utcnow().isoformat(), f"Found via adaptive search: {adaptive_query}"]
                                        with file_lock:
                                            with open(OUTPUT_FILE, "a", newline='') as f:
                                                writer = csv.writer(f)
                                                writer.writerow(row)
                    
                    time.sleep(random.randint(1, 3))
                    
                except Exception as e:
                    logger.debug(f"🔍 Adaptive search error: {e}")
                    continue
    
    logger.info(f"✅ Smart keyword search completed. Found {len(discovered_from_search)} unique onion URLs")
    logger.info(f"🧠 Discovered {len(discovered_keywords)} new keywords for future searches")
    return discovered_from_search

def process_url(url, depth, max_depth):
    """Worker function to process a single URL"""
    global seen, discovered, page_counter, addresses_found, last_processed_url, max_depth_urls
    
    # Ensure URL has http:// prefix
    if not url.startswith('http'):
        url = f"http://{url}"
    
    raw_host = urlparse(url).hostname
    if not raw_host:
        logger.error(f"❌ Invalid URL format: {url}")
        return []
    
    clean_host = extract_clean_onion(raw_host)
    if not clean_host:
        return []
    
    # Thread-safe check for seen URLs
    with seen_lock:
        if clean_host in seen or depth > max_depth:
            return []
        seen.add(clean_host)
    
    logger.info(f"🌐 Visiting: {url} | Depth: {depth}")
    
    try:
        # Create a new session for each thread to avoid conflicts
        thread_session = requests.Session()
        thread_session.proxies = {
            "http": TOR_SOCKS_PROXY,
            "https": TOR_SOCKS_PROXY
        }
        thread_session.headers.update({"User-Agent": USER_AGENT})
        
        # Reduced timeout for faster failure detection
        resp = thread_session.get(url, timeout=15)
        logger.info(f"🔎 HTTP status for {url}: {resp.status_code}")
        new_links = []
        
        # Always extract onion links for crawling, regardless of keywords
        extracted_links = extract_onion_links(resp.text, url)
        logger.info(f"🔗 Found {len(extracted_links)} onion links on {url}")
        if extracted_links:
            logger.info(f"🔗 Links: {list(extracted_links)}")
        
        # NEW: Perform dynamic searches if search forms are detected
        if resp.status_code == 200:
            dynamic_links = perform_dynamic_searches(resp.text, url, depth)
            extracted_links.update(dynamic_links)
            logger.info(f"🔍 Dynamic searches added {len(dynamic_links)} links to extraction")
        
        # Save all discovered onion links to output file (not just those with keywords)
        with discovered_lock:
            for link in extracted_links:
                if link not in discovered:
                    discovered.add(link)
                    row = [f"http://{link}", url, depth, datetime.utcnow().isoformat(), extract_title(resp.text)]
                    logger.info(f"➕ Discovered: {link}")
                    with file_lock:
                        with open(OUTPUT_FILE, "a", newline='') as f:
                            writer = csv.writer(f)
                            writer.writerow(row)
        
        # Track URLs at maximum depth for deeper crawling
        if depth == max_depth:
            with discovered_lock:
                max_depth_urls.add(url)
                logger.info(f"🔍 Added to max depth URLs: {url}")
        
        # Add all extracted links to queue for crawling (if within depth limit)
        for link in extracted_links:
            if depth + 1 <= max_depth:
                new_links.append((f"http://{link}", depth + 1))
                logger.debug(f"📥 Queued for depth {depth + 1}: {link}")
        
        # Thread-safe page counter update
        with page_counter_lock:
            global page_counter
            page_counter += 1
            if page_counter % ROTATE_EVERY_N == 0:
                rotate_tor_identity()
        
        sleep_time = random.randint(*SLEEP_BETWEEN_REQUESTS)
        logger.debug(f"⏳ Sleeping {sleep_time}s")
        time.sleep(sleep_time)
        
        # Extract cryptocurrency addresses
        addresses = extract_crypto_addresses(resp.text)
        if addresses:
            logger.info(f"💰 Found {len(addresses)} cryptocurrency addresses on {url}")
            with file_lock:
                with open(ADDRESSES_FILE, "a", newline='') as f:
                    writer = csv.writer(f)
                    for address in addresses:
                        writer.writerow([address, url, depth, datetime.utcnow().isoformat()])
            
            # Update global address counter
            with page_counter_lock:
                global addresses_found
                addresses_found += len(addresses)
        
        # Update last processed URL
        last_processed_url = url
        
        return new_links
        
    except requests.exceptions.ConnectionError as e:
        logger.debug(f"🔌 Connection failed for {url}: {str(e)[:100]}...")
        return []
    except requests.exceptions.Timeout as e:
        logger.debug(f"⏰ Timeout for {url}: {str(e)[:100]}...")
        return []
    except requests.exceptions.RequestException as e:
        logger.debug(f"🌐 Request failed for {url}: {str(e)[:100]}...")
        return []
    except Exception as e:
        logger.error(f"❌ Unexpected error visiting {url}: {e}")
        # Save restart info when an unexpected error occurs
        save_restart_info(url, depth, e)
        return []

def save_max_depth_urls():
    """Save max depth URLs to a file for use as new seed URLs"""
    if not max_depth_urls:
        logger.info("📝 No max depth URLs to save")
        return
    
    max_depth_file = f"max_depth_urls_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(max_depth_file, 'w') as f:
            for url in sorted(max_depth_urls):
                f.write(f"{url}\n")
        logger.info(f"💾 Saved {len(max_depth_urls)} max depth URLs to {max_depth_file}")
        logger.info(f"🔍 Use these URLs as new seed URLs for deeper crawling")
    except Exception as e:
        logger.error(f"❌ Failed to save max depth URLs: {e}")

def crawl(start_urls, max_depth=2, resume=False, no_search=False):
    global seen, discovered, page_counter, addresses_found, last_processed_url, max_depth_urls
    
    start_time = datetime.utcnow()
    
    # Load previous progress if resuming
    if resume:
        saved_queue, saved_seen, saved_discovered, saved_counter, saved_addresses, saved_last_processed_url, saved_max_depth_urls = load_progress()
        if saved_queue is not None:
            queue = saved_queue
            seen.update(saved_seen)
            discovered.update(saved_discovered)
            page_counter = saved_counter
            addresses_found = saved_addresses
            last_processed_url = saved_last_processed_url
            max_depth_urls.update(saved_max_depth_urls)
            logger.info(f"🔄 Resuming with {len(queue)} URLs in queue")
        else:
            # No progress file found, start fresh but still in resume mode
            queue = [(url if url.startswith('http') else f"http://{url}", 0) for url in start_urls]
            logger.info("🆕 No progress file found, starting fresh crawl")
    else:
        # Pre-populate the 'seen' set with URLs from previous runs
        with seen_lock:
            seen.update(load_previously_discovered())
        
        if no_search:
            # Skip keyword search but still extract links from known directories for broad discovery
            logger.info("🌐 Phase 1: Extracting links from known directories (keyword search skipped)...")
            broad_links = set()
            for dir_url in LINK_DIRECTORY_URLS:
                links = extract_links_from_directory(dir_url)
                logger.info(f"🌐 {dir_url}: Found {len(links)} links")
                broad_links.update(links)
            logger.info(f"🌐 Total unique links from directories: {len(broad_links)}")
            
            # Add directory links to queue
            directory_urls = [(f"http://{link}", 0) for link in broad_links]
            
            # Also add original seed URLs
            seed_urls = [(url if url.startswith('http') else f"http://{url}", 0) for url in start_urls]
            
            # Combine directory links and seed URLs
            queue = directory_urls + seed_urls
            logger.info(f"🚀 Starting crawl with {len(queue)} URLs (directory links: {len(directory_urls)}, seeds: {len(seed_urls)})")
        else:
            # --- Broad Phase: Extract all links from known directories ---
            logger.info("🌐 Phase 1: Extracting links from known directories...")
            broad_links = set()
            for dir_url in LINK_DIRECTORY_URLS:
                links = extract_links_from_directory(dir_url)
                logger.info(f"🌐 {dir_url}: Found {len(links)} links")
                broad_links.update(links)
            logger.info(f"🌐 Total unique links from directories: {len(broad_links)}")

            # --- Targeted Phase: Search for keywords on search engines ---
            logger.info("🔍 Phase 2: Searching keywords on search engines...")
            discovered_from_search = search_keywords_on_engines()
            logger.info(f"🔍 Total unique links from keyword search: {len(discovered_from_search)}")

            # --- Prioritize links: keyword-relevant first, then others ---
            all_links = set(broad_links) | set(discovered_from_search)
            prioritized = []
            non_prioritized = []
            for link in all_links:
                # Optionally fetch title/snippet for better scoring, but for now just use URL
                score = keyword_relevance_score(link)
                if score > 0:
                    prioritized.append((link, 0, score))
                else:
                    non_prioritized.append((link, 0, 0))
            # Sort prioritized by score descending
            prioritized.sort(key=lambda x: -x[2])
            # Remove score for queue
            prioritized = [(x[0], x[1]) for x in prioritized]
            non_prioritized = [(x[0], x[1]) for x in non_prioritized]

            # Also add original seed URLs (in case they're not search engines)
            seed_urls = [(url if url.startswith('http') else f"http://{url}", 0) for url in start_urls]

            # Combine: prioritized, then non-prioritized, then seeds
            queue = prioritized + non_prioritized + seed_urls
            logger.info(f"🚀 Starting crawl with {len(queue)} URLs (prioritized: {len(prioritized)}, non-prioritized: {len(non_prioritized)}, seeds: {len(seed_urls)})")

    # Check for restart info
    restart_info = load_restart_info()
    if restart_info and not resume:
        logger.info(f"💡 To resume from last crash, run with --resume flag")
    
    if not os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["onion_url", "source", "depth", "timestamp", "title"])

    # Create addresses file if it doesn't exist
    if not os.path.exists(ADDRESSES_FILE):
        with open(ADDRESSES_FILE, "w", newline='') as f:
            writer = csv.writer(f)
            writer.writerow(["address", "source_url", "depth", "timestamp"])

    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            while queue:
                # Save progress periodically
                if len(queue) % 10 == 0:  # Save every 10 URLs processed
                    save_progress(queue, seen, discovered)
                    
                    # Calculate and log statistics
                    elapsed = datetime.utcnow() - start_time
                    urls_per_minute = page_counter / (elapsed.total_seconds() / 60) if elapsed.total_seconds() > 0 else 0
                    logger.info(f"📊 Progress: {page_counter} processed, {len(discovered)} discovered, {addresses_found} addresses found, {len(queue)} queued, {urls_per_minute:.1f} URLs/min")
                    if last_processed_url:
                        logger.info(f"📍 Last processed: {last_processed_url}")
                
                # Submit up to MAX_WORKERS tasks
                futures = []
                for _ in range(min(MAX_WORKERS, len(queue))):
                    if queue:
                        url, depth = queue.pop(0)
                        future = executor.submit(process_url, url, depth, max_depth)
                        futures.append(future)
                
                # Collect results and add new URLs to queue
                for future in as_completed(futures):
                    try:
                        new_links = future.result()
                        queue.extend(new_links)
                    except Exception as e:
                        logger.error(f"❌ Worker error: {e}")
                
                # Small delay to prevent overwhelming the system
                if queue:
                    time.sleep(1)
        
        # Final statistics
        total_time = datetime.utcnow() - start_time
        logger.info("✅ Crawl completed successfully!")
        logger.info(f"📈 Final stats: {page_counter} URLs processed, {len(discovered)} discovered, {addresses_found} addresses found in {total_time}")
        if last_processed_url:
            logger.info(f"📍 Last processed URL: {last_processed_url}")
        
        # Save max depth URLs for deeper crawling
        save_max_depth_urls()
        
    except KeyboardInterrupt:
        logger.info("⏹️  Crawl interrupted by user")
        save_progress(queue, seen, discovered)
        logger.info(f"💾 Progress saved. Resume with --resume flag")
        if last_processed_url:
            logger.info(f"📍 Last processed URL: {last_processed_url}")
        save_max_depth_urls()
        raise
    except Exception as e:
        logger.error(f"❌ Crawl failed: {e}")
        save_progress(queue, seen, discovered)
        save_restart_info(queue[0][0] if queue else "unknown", queue[0][1] if queue else 0, e)
        if last_processed_url:
            logger.info(f"📍 Last processed URL: {last_processed_url}")
        save_max_depth_urls()
        raise

def extract_links_from_directory(url):
    """Extract all onion links from a known directory page."""
    try:
        resp = session.get(url, timeout=20)
        if resp.status_code == 200:
            return extract_onion_links(resp.text, url)
        else:
            logger.warning(f"⚠️ Directory {url} returned status {resp.status_code}")
    except Exception as e:
        logger.error(f"❌ Error extracting from directory {url}: {e}")
    return []

def keyword_relevance_score(text, keywords=KEYWORDS):
    """Score a text (title or snippet) for keyword relevance."""
    text = text.lower()
    return sum(1 for kw in keywords if kw in text)

# ----------------------------
# Run
# ----------------------------
if __name__ == "__main__":
    import sys
    
    # Check for command line arguments
    resume = "--resume" in sys.argv
    verbose = "--verbose" in sys.argv
    quiet = "--quiet" in sys.argv
    no_search = "--no-search" in sys.argv
    
    # Set logging level based on arguments
    if quiet:
        logging.getLogger().setLevel(logging.WARNING)
    elif verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    else:
        # Default: show INFO and above, but not DEBUG
        logging.getLogger().setLevel(logging.INFO)
        # Also disable DEBUG for specific loggers
        logging.getLogger('urllib3').setLevel(logging.WARNING)
        logging.getLogger('requests').setLevel(logging.WARNING)
        logging.getLogger('requests.packages.urllib3').setLevel(logging.WARNING)
    
    if resume:
        logger.info("🔄 Resuming previous crawl...")
        crawl(SEED_URLS, MAX_DEPTH, resume=True)
    else:
        logger.info("🚀 Starting new crawl...")
        logger.info("💡 Use --resume to continue from where you left off")
        logger.info("💡 Use --verbose for detailed logging, --quiet for minimal output")
        logger.info("💡 Use --no-search to skip keyword search phase")
        crawl(SEED_URLS, MAX_DEPTH, no_search=no_search)