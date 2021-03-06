
import re
import requests
import csv
from fifo_q import Queue as Q
from utils import random_sleep
from document_parser import get_soup

#获取电影movie_info{rating,name,year}
def get_movie_info(soup):
    rating = soup.find('strong', {'class': 'll rating_num'}).text

    movie_name = soup.find('span', {'property': "v:itemreviewed"}).text
    year = soup.find('span', {'class': 'year'}).text

    movie_info = {
        'rating': rating,
        'name': movie_name,
        'year': year.replace('(', '').replace(')', '')
    }

    return movie_info

#获取recommedation list[name,id]
def get_recommends_list(soup):

    recommends = soup.find('div', {'class': 'recommendations-bd'})
    names = [a['alt'] for a in recommends.find_all('img')]
    ids = [re.search('subject/(.*)/', a['href']).group(1)
             for ii, a in enumerate(recommends.find_all('a'))
             if ii % 2 == 0]

    print("get_recommends_start, names: ", names, " ids: ", ids)
    return list(zip(names, ids))

#获取url
def get_subject_page_by_movie_id(movie_id):
    return "https://movie.douban.com/subject/{}/".format(movie_id)

#抽取信息
def extract_movie_info(f):
    def _extract(movie_id):
        url = get_subject_page_by_movie_id(movie_id)
        r = requests.get(url)
        print("extract move info _url: ", url, ": status_code: ", r.status_code)
        if r.status_code == 200: return f(get_soup(r.text))
        elif r.status_code == 403: raise LookupError('error connection when getting: {}'.format(movie_id))
        else: raise FileNotFoundError('movie: {} not found'.format(movie_id))
    return _extract

#构造新函数
get_movie_recommendation = extract_movie_info(get_recommends_list)
get_movie_abstract = extract_movie_info(get_movie_info)

#给队列push_ID函数
def add_ids_to_queue(queue, recommendations):
    [queue.push(ID) for name, ID in recommendations]
    return queue

#保存（number, movie_id, name, year, rating）信息至文件info_file，并输出（number, movie_info）
def movie_info_saver(info_file):
    csvfile = open(info_file, 'a+')#语法不懂
    spamwrite = csv.writer(csvfile)#语法不懂
    spamwrite.writerow(['id', 'douban_id', 'name', 'year', 'rating'])

    def _save(number, movie_id):
        movie_info = get_movie_abstract(movie_id)
        print("{}: {}".format(number, movie_info))
        spamwrite.writerow([
            number, movie_id, movie_info['name'], movie_info['year'], movie_info['rating']
        ])

    return _save



def get_recommendation_by_bfs(movie_id):  #

    visted = set()

    max_length = 100
    queue = Q(length=max_length)

    for _id in movie_id: queue.push(_id)

    number = 0

    #save_info = movie_info_saver('movie_info/movie_info_from_{}.csv'.format(movie_id[0]))
    save_info = movie_info_saver('movie_info/movies_id1020.csv')

    while 0 <= number < max_length:
        movie_id = queue.pop()

        if movie_id in visted: continue
        else: visted.add(movie_id)

        try:
            recommendations = get_movie_recommendation(movie_id)
            save_info(number, movie_id)
        except LookupError as e:
            print(e)
            break
        except FileNotFoundError as e:
            print(e)
            continue
        except Exception as e:
            continue

        queue = add_ids_to_queue(queue, recommendations)

        print()
        print()

        number += 1

        random_sleep()

    for ID in queue:
        try: save_info(number, ID)  #与99行功能重复会导致，movies_id.csv中的ID会重复。
        except LookupError as e: break
        number += 1
    print(number)
    return number


if __name__ == '__main__':
    # movie_info = get_movie_info(get_soup(get_html_doc('movie_subject.html')))
    # recommends = get_recommends_list(get_soup(get_html_doc('movie_subject.html')))
    # print(movie_info)
    # print(recommends)

    ids = ['26985127']

    movies = get_recommendation_by_bfs(ids)
    print(movies)
