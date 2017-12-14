#http://www.markhneedham.com/blog/2015/01/19/pythonnltk-finding-the-most-common-phrases-in-how-i-met-your-mother/
# https://inzaniak.github.io/pybistuffblog/posts/2017/04/20/python-count-frequencies-with-nltk.html
# https://stackoverflow.com/questions/14364762/counting-n-gram-frequency-in-python-nltk

from collections import Counter
from itertools import combinations
import nltk
import numpy as np
#nltk.download('punkt')
import glob
import matplotlib.pyplot as plt
from utils.process_lyrics import *
np.random.seed(12)

def get_word_ranks(cnt1, pos1, cnt2, pos2, master_labels, n_words, pad):
    labels1, count1 = zip(*cnt1.most_common(10*n_words))
    labels2, count2 = zip(*cnt2.most_common(10*n_words))
    for i in range(n_words):
        l = labels1[i]
        if l not in master_labels[0:n_words]:
            try:
                _c, _r = cnt2[l], labels2.index(l)
                pos2.append(min(_r,n_words))
            except:
                pos2.append(n_words)
            master_labels.append(l)
            pos1.append(i)
    return master_labels, pos1, pos2

# https://stackoverflow.com/questions/11763613/python-list-of-ngrams-with-frequencies
####### Main Functions ###########
def get_stats(dir, norm, n_songs, print_=0):
    files = glob.glob('%s/*.txt'%dir)
    cnt, bi_cnt, tri_cnt = Counter(), Counter(), Counter()
    words_per_song = 0
    n_processed_songs = 0
    min_words_per_song = 15     #ignore instrumentals
    for f in files:
        #lyric = get_clean_lyric(f)
        lyric = process_song(f, 'word')
        if len(lyric) > min_words_per_song:
            bi_lyric=nltk.FreqDist(nltk.ngrams(lyric, 2))
            tri_lyric=nltk.FreqDist(nltk.ngrams(lyric, 3))
            
            #normalize
            normalize = 1
            n_words = len(lyric)
            if norm == 1:
                normalize = float(n_words*n_songs)
            
            words_per_song += float(n_words)/float(n_songs)
            for l in lyric:
                cnt[l] += 1/normalize
            for b in bi_lyric:
                bi_cnt[b] += 1/normalize
            for t in tri_lyric:
                tri_cnt[t] += 1/normalize

            n_processed_songs += 1
        if n_processed_songs > n_songs:
            break

    if print_ == 1:
        print("########%s########"%dir)
        print("----Top single words:----")
        print(cnt.most_common(50))
        print("----Top paired words:----")
        print(bi_cnt.most_common(20))
        print("----Top tri-words:----")
        print(tri_cnt.most_common(20))
        print("Total number of unique words = %d"%len(cnt))
        print("Avg words per song = %f"%words_per_song)

    return [cnt, bi_cnt, tri_cnt, words_per_song]

####### Arguments ###########
if __name__ == '__main__':
    dirs = ['playlists/edm','playlists/hip-hop','playlists/rock', 'playlists/country', 'playlists/pop']
    #dirs = ['playlists/edm','playlists/pop']
    norm = 0
    n_songs = 996
    n_grams = 1
    n_common_words = 80

    #get data
    data = {}
    for i in range(len(dirs)):
        data[i] = get_stats(dirs[i],norm,n_songs)

    #plot common pairs between genres
    plot_common = 1
    if plot_common == 1:
        combos = list(combinations(range(len(dirs)),2))
        pad = 8
        for i1,i2 in combos:
            master_labels, pos1, pos2  = [], [], []
            master_labels, pos1, pos2 = get_word_ranks(data[i1][n_grams-1], pos1, data[i2][n_grams-1], pos2, master_labels, n_common_words, pad)
            master_labels, pos2, pos1 = get_word_ranks(data[i2][n_grams-1], pos2, data[i1][n_grams-1], pos1, master_labels, n_common_words, pad)
            
            #plot prep
            plt.figure(figsize=(10,8))
            plt.plot([0,n_common_words], [0,n_common_words])
            plt.plot([0,n_common_words], [0,n_common_words/2], 'g')
            plt.plot([0,n_common_words/2], [0,n_common_words], 'g')
            plt.plot([0,n_common_words],[n_common_words,n_common_words],'r--')
            plt.plot([n_common_words,n_common_words],[0,n_common_words],'r--')
            #plt.fill_between([0,n_common_words+pad],[n_common_words,n_common_words],[n_common_words+pad,n_common_words+pad], facecolor='red',alpha=0.5, linewidth=0)
            #plt.axvspan(n_common_words, n_common_words+pad, alpha=0.5, color='red')
            plt.plot(pos1, pos2, '.', color='black')
            for i in range(len(pos1)):
                rot, buffx, buffy = 0, 0.5, -1
                la = master_labels[i]
                if la == 'nigga':
                    la = 'ni**a'
                elif la == 'niggas':
                    la = 'ni**as'
                if pos2[i] == n_common_words:
                    rot, buffx, buffy = 90, 0, 5
                plt.text(pos1[i]+buffx, pos2[i]+buffy, la, size=9, rotation=rot)
            name1, name2 = dirs[i1].split('playlists/')[1], dirs[i2].split('playlists/')[1]
            plt.xlabel('%s rank'%name1)
            plt.ylabel('%s rank'%name2)
            plt.xlim([0,n_common_words+pad])
            plt.ylim([0,n_common_words+pad])
            plt.savefig('images/wordcorr_%s_%s.png'%(name1,name2))
            plt.clf()

    #plot word frequency
    plot_words = 0
    if plot_words == 1:
        ylabel = 'total counts'
        if norm == 1:
            ylabel = 'counts/(song*word)'
        for i in range(len(data)):
            labels, count = zip(*data[i][n_grams-1].most_common(n_common_words))
            #ran = np.arange(1,len(count)+1)
            #print(zip(labels,count,ran,ran**(0.55)*np.asarray(count)))
            #labels, count = spam_filter(labels, count)
            x, name = range(len(count)), dirs[i].split('playlists/')[1]
            plt.plot(x, count, label='avg. words per song=%d'%data[i][3])
            plt.xticks(x, labels, rotation='vertical',fontsize=11)
            plt.ylabel(ylabel)
            plt.legend(fontsize=12)
            plt.title(name)
            plt.savefig('images/worddist_%s.png'%name)
            plt.clf()

    #get unique words for each genre
    get_unique = 1
    if get_unique == 1:
        labels, counts = [], []
        cold_words = {}     #words popular in other genres but not this one
        unique_words = {}   #words popular in this genre and no other
        for i in range(len(dirs)):
            l, c = zip(*data[i][n_grams-1].most_common(10*n_common_words))
            labels.append(l)
            counts.append(c)
            cold_words[i], unique_words[i] = [], []
        for i in range(len(dirs)):
            for j in range(2*n_common_words):
                label = labels[i][j]
                ranks_ = np.zeros(0,dtype='int')     #rank for all dirs
                counts_ = np.zeros(0,dtype='int')
                for k in range(len(dirs)):
                    try:
                        index = labels[k].index(label)
                        ranks_ = np.append(ranks_,index)
                        counts_ = np.append(counts_,counts[k][index])
                    except:
                        ranks_ = np.append(ranks_,10*n_common_words)
                        counts_ = np.append(counts_,0)
                if len(np.where(1.5*j + 2 < ranks_)[0]) == len(ranks_)-1:
                    unique_words[i].append(label)
                if label in ['sun']:
                    print(label,ranks_,counts_)
                if (len(np.where(np.max(ranks_)/1.5 - 2 < ranks_)[0]) == 1) and (len(np.where(np.min(counts_)*1.5 + 3 > counts_)[0]) == 1):
                    if label not in cold_words[np.argmax(ranks_)]:
                        cold_words[np.argmax(ranks_)].append(label)
        
        print("*******unique words*******")
        for i in range(len(dirs)):
            print(dirs[i],unique_words[i])
        print("*******cold words*******")
        for i in range(len(dirs)):
            print(dirs[i],cold_words[i])
