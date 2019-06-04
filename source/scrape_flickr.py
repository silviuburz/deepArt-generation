import flickrapi
import urllib.request
import os
import argparse
from multiprocessing.pool import ThreadPool
from tqdm import tqdm

def args_parser():
    parser = argparse.ArgumentParser(description="Scrape flickr for images based on keyword")

    parser.add_argument("-kw", "--keywords", type=str, default="nude painting", dest="keywords", nargs= "+",
                        help="String which keywords to scrape. If more keywords should be scraped use this parameter several times.\
                        e.g --keyword 'nude art' --keyword 'landscape'. Default: 'nude painting'")
    parser.add_argument("-sp", "--save_path", type=str, dest="save_path", default="nude-painting",
                        help="Directory where the images should be saved. The images will be saved to 'data/save_path' \
                        subdirectory where <save_path> needs to be defined. Default 'nude-painting'")
    parser.add_argument("-l", "--limit", type=int, dest="limit", default=30000,
                        help="Maximum number of images to scrape from flickr. Default: 30000")
    parser.add_argument("-nw", "--n_workers", type=int, default=4, dest="n_workers",
                        help="For downloading images split the download into <n_workers> processes. Default: 4")

    args = parser.parse_args()

    return args

def crawl_flickr(keyword, limit, flickr):
    print("Crawl keyword: {}".format(keyword))
    #https://www.flickr.com/services/api/flickr.photos.search.html
    photos = flickr.walk(text=keyword,
                         tag_mode="all",
                         extras="url_c",
                         per_page=500,
                         sort="relevance")
    urls = [None] * limit
    for i, photo in tqdm(enumerate(photos), total=limit):

        if i == limit:
            break

        urls[i] = photo.get("url_c")
        ## print out every 1000 urls information
        if i % 1000 == 0 and i != 0 or i == limit-1:
            tqdm.write("Retrieved url number {}/{}".format(i+1 if i == limit-1 else i, limit))

    urls = [url for url in urls if url is not None]

    return urls

def download_image(tuple):
    filename, url = tuple
    urllib.request.urlretrieve(url, filename)
    return 1


if __name__ == '__main__':

    ## Flickr API credentials:
    API_key = "079921da9a005d9590836da31229f7f2"
    API_secret_key = "62ab87626c9b4fb3"
    # Flickr api access key
    flickr = flickrapi.FlickrAPI(API_key, API_secret_key, cache=True)


    print("Python script to scrape images from flickr and download images.")
    args = args_parser()
    print(args)

    keywords = args.keywords
    limit = args.limit
    save_path = "../data/" + args.save_path
    n_workers = args.n_workers

    if not os.path.exists(save_path):
        os.makedirs(save_path)


    ## Scrape links:
    if isinstance(keywords, list) and len(keywords) > 1:
        all_urls = [crawl_flickr(keyword, limit, flickr) for keyword in keywords]
        all_urls = [item for sublist in all_urls for item in sublist]
    else:
        all_urls = crawl_flickr(keywords, limit, flickr)

    ## remove duplicates
    all_urls = list(set(all_urls))
    print("Total number of scraped links for keywords {} is: {}".format(str(keywords), len(all_urls)))

    ## Download images:
    # Preprare tupled list to pass over to multithread
    all_urls = [("{}/{}.jpg".format(save_path, i), url) for i, url in enumerate(all_urls)]
    results = ThreadPool(n_workers).imap_unordered(func=download_image, iterable=all_urls)

    n_sucess = 0
    for sucess in tqdm(results, total=len(all_urls)):
        n_sucess += sucess
        ## print out every 100
        if n_sucess % 100 == 0 and n_sucess != 0 or n_sucess == len(all_urls):
            tqdm.write("Downloaded {}/{}".format(n_sucess, len(all_urls)))

    print("Downloaded {} images and stored at {}".format(n_sucess, save_path))