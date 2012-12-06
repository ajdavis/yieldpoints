"""An example for :class:`~yieldpoints.WaitAny`, :class:`~yieldpoints.WithTimeout`,
and :class:`~yieldpoints.CancelAll`: download several web pages at once and
take action as each completes. After 0.5 seconds, stop waiting.
"""

# start-file
import time

from tornado import web, gen, ioloop, httpclient

import yieldpoints


class PageRaceHandler(web.RequestHandler):
    """A 'page race': start downloading many pages at once, and see how long
    each takes.
    """
    @web.asynchronous
    @gen.engine
    def get(self):
        urls = set([
            'http://google.com', 'http://apple.com', 'http://microsoft.com',
            'http://amazon.com'])

        self.write('<table border="1">')

        start = time.time()
        def duration():
            return time.time() - start

        # Set max_clients so all fetches can happen at once
        client = httpclient.AsyncHTTPClient(max_clients=len(urls))

        # Start all the fetches
        for url in urls:
            client.fetch(url, callback=(yield gen.Callback(url)))

        # Handle them as they complete
        pending_urls = urls.copy()
        while pending_urls:
            try:

                url, response = yield yieldpoints.WithTimeout(
                    start + 0.5, yieldpoints.WaitAny(pending_urls))

            except yieldpoints.TimeoutException:
                self.finish("""
                    </table>

                    <p>These URLs did not complete after %.1f seconds: %s</p>
                """ % (duration(), ', '.join(pending_urls)))

                # Avoid LeakedCallbackError
                yield yieldpoints.CancelAll()

                # Quit this coroutine
                raise StopIteration

            pending_urls.remove(url)
            self.write("""
                <tr>
                    <td>%s</td>
                    <td>HTTP %s</td>
                    <td>%.1f seconds</td>
                </tr>
            """ % (url, response.code, duration()))

            yield gen.Task(self.flush)

        self.finish("""
            </table>

            <p>Completed all in %.1f seconds</p>
        """ % duration())


if __name__ == '__main__':
    print 'Listening on http://localhost:8888'
    web.Application([('.*', PageRaceHandler)], debug=True).listen(8888)
    ioloop.IOLoop.instance().start()
