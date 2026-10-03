"""Sample corpus, part 3 of 3 - Algorithms, Web Development, Java, Python
and DevOps (16 original educational documents).

The five algorithm documents are the pedagogical core of the project: they
match the concepts implemented in /algorithms one-to-one.
"""

ARTICLES: list[dict] = [
    {
        "slug": "searching-algorithms",
        "title": "Searching Algorithms: Linear, Binary, Hash and Trie",
        "category": "Algorithms",
        "author": "Prof. S. Iyer",
        "url": "nexasearch://searching-algorithms",
        "keywords": "searching, linear search, binary search, hash search, trie search, complexity",
        "content": (
            "Searching is the problem of locating a target in a collection, and its cost depends "
            "on two things: the algorithm and the data structure.\n\n"
            "Linear search compares the target with each element in turn. It works on unsorted "
            "data and costs O(n) in the average and worst cases, but only O(1) in the best case "
            "where the target is first. It is the only choice when data arrives unsorted and "
            "occasional lookups are expected.\n\n"
            "Binary search requires sorted data and repeatedly halves the range, so it costs "
            "O(log n). It is the algorithm behind database B-trees and is why sorted indexes are "
            "worth their maintenance cost. Its weakness is the sorting precondition, and "
            "insertion into a sorted array is O(n).\n\n"
            "Hash search computes a bucket address from the key, giving O(1) average lookup. It "
            "trades ordering and worst case: every collision lengthens a chain, so load factor "
            "must be controlled by rehashing.\n\n"
            "A trie stores prefixes as paths, so lookup costs O(L) where L is the word length, "
            "completely independent of how many words are stored, and prefix search falls out for "
            "free. The price is memory: one node per distinct prefix. A search engine needs all "
            "four, which is why this project implements all four: the corpus is scanned linearly "
            "as a baseline, sorted ids are probed by binary search, postings are fetched through "
            "the hash table, and the vocabulary plus autocomplete come from the trie."
        ),
    },
    {
        "slug": "sorting-algorithms",
        "title": "Sorting Algorithms: Merge, Quick, Heap and the Space Trade-off",
        "category": "Algorithms",
        "author": "Prof. S. Iyer",
        "url": "nexasearch://sorting-algorithms",
        "keywords": "sorting, merge sort, quick sort, heap sort, stability, in place, lower bound",
        "content": (
            "Sorting is used for ordered output, for binary search, for grouping and for "
            "deterministic presentation. There is a lower bound of Omega(n log n) comparisons in "
            "the comparison model, because a comparison has only two outcomes and a sorted "
            "output requires n! distinct orderings, so the decision tree needs at least log2(n!) "
            "nodes.\n\n"
            "Merge sort splits the array, sorts the halves and merges them. The merge step is "
            "linear, and because the split is always even the recurrence T(n) = 2T(n/2) + n "
            "gives Theta(n log n) for every input, including already sorted data. It needs a "
            "Theta(n) buffer and is stable, so equal keys keep their original order, which "
            "matters when ties are broken by an earlier relevance signal. This is why the search "
            "results in this project are ordered with merge sort.\n\n"
            "Quick sort partitions around a pivot. It sorts in place with only O(log n) extra "
            "stack space and is usually the fastest in practice because of cache locality, but "
            "the worst case is Theta(n^2). Median-of-three and randomised pivots make that "
            "worst case vanishingly unlikely on real data.\n\n"
            "Heap sort builds a binary heap in O(n) using Floyd's method and then extracts the "
            "maximum n times at O(log n), giving Theta(n log n) time with O(1) extra space. It is "
            "the only comparison sort with both bounds optimal, but poor cache behaviour makes "
            "it slower than quick sort in practice.\n\n"
            "Non-comparison sorts such as counting and radix sort beat the lower bound by "
            "exploiting the structure of the keys, at the cost of extra memory."
        ),
    },
    {
        "slug": "string-matching-algorithms",
        "title": "String Matching: Naive, KMP and Rabin-Karp",
        "category": "Algorithms",
        "author": "Prof. S. Iyer",
        "url": "nexasearch://string-matching-algorithms",
        "keywords": "string matching, kmp, lps array, rabin karp, rolling hash, z algorithm",
        "content": (
            "String matching asks where a pattern occurs in a text. For text of length n and "
            "pattern of length m, the naive matcher is O((n - m + 1) * m) in the worst case "
            "because it restarts the text pointer after every mismatch.\n\n"
            "KMP removes the restart. Before searching it builds the LPS array, where lps[i] is "
            "the length of the longest proper prefix of the pattern up to i that is also its "
            "suffix. On a mismatch at pattern position j, the matcher sets j to lps[j - 1] "
            "instead of zero, because the matched part is a suffix of the new candidate. The "
            "text pointer never moves backwards, so the search is O(n + m) with O(m) space, and "
            "overlapping matches such as abab found in ababab are reported correctly.\n\n"
            "Rabin-Karp hashes the pattern once and slides a window across the text, recomputing "
            "each window hash in O(1) by removing the outgoing character's contribution and "
            "adding the incoming one. Only windows whose hash matches are verified character by "
            "character. Hashing is many-to-one, so false positives are expected, and the "
            "verification step is what makes the result correct. Average time is O(n + m), worst "
            "case O(n * m) when every window collides. Its real advantage is matching many "
            "patterns in a single pass over the text.\n\n"
            "The Z-algorithm computes the longest prefix match at every position, giving O(n) "
            "matching plus pattern matching at every prefix. Aho-Corasick builds a trie of "
            "patterns and reports all of them in one pass, at O(total pattern length) "
            "amortised per character.\n\n"
            "In this project both KMP and Rabin-Karp run on quoted phrases and their match "
            "positions are compared as a correctness cross-check."
        ),
    },
    {
        "slug": "graph-algorithms",
        "title": "Graph Algorithms: BFS, DFS, Dijkstra and MST",
        "category": "Algorithms",
        "author": "Prof. S. Iyer",
        "url": "nexasearch://graph-algorithms",
        "keywords": "graph algorithm, breadth first search, depth first search, dijkstra, topological sort, minimum spanning tree",
        "content": (
            "A graph models relationships between objects: vertices and edges. BFS and DFS are "
            "the two fundamental traversals and everything else is built on them.\n\n"
            "BFS uses a first-in first-out queue, so it visits vertices in non-decreasing "
            "distance from the source. Because the first path found to a vertex has the fewest "
            "edges, BFS gives shortest paths in unweighted graphs in O(V + E) time. It also "
            "produces the level structure, detects bipartite graphs, and finds all components.\n\n"
            "DFS uses a stack, so it goes as deep as possible before backtracking, in O(V + E) "
            "time and O(V) space. Recursion depth can reach V, which is a practical limit. DFS "
            "supports cycle detection through colouring, topological sorting of a directed "
            "acyclic graph, and strongly connected components.\n\n"
            "Dijkstra's algorithm generalises BFS to weighted graphs. It repeatedly settles the "
            "unvisited vertex with the smallest tentative distance, which is why it needs a "
            "priority queue. With a binary heap it costs O((V + E) log V). The greedy step is "
            "valid only for non-negative weights; with negative weights use Bellman-Ford, "
            "O(V * E), which also detects negative cycles.\n\n"
            "The minimum spanning tree connects every vertex at minimum total weight. "
            "Kruskal's algorithm sorts edges and adds them when they join different components, "
            "using union-find, and costs O(E log E). Prim's algorithm grows one tree from a "
            "source vertex and costs O(E log V) with a heap.\n\n"
            "The document graph in this project uses BFS and DFS for related-document "
            "traversals and Dijkstra on similarity-weighted edges to show shortest paths."
        ),
    },
    {
        "slug": "dynamic-programming",
        "title": "Dynamic Programming, Greedy Choice and Memoisation",
        "category": "Algorithms",
        "author": "Prof. S. Iyer",
        "url": "nexasearch://dynamic-programming",
        "keywords": "dynamic programming, memoisation, optimal substructure, greedy algorithm, bellman ford, knapsack",
        "content": (
            "Dynamic programming applies to problems with two properties. Optimal substructure "
            "means an optimal solution is composed of optimal solutions to subproblems. "
            "Overlapping subproblems means the same subproblem is solved again and again. It "
            "trades space for time, converting exponential recomputation into a single evaluation "
            "per state.\n\n"
            "The procedure is to define the state, write the recurrence relating states, choose "
            "an evaluation order such as increasing state size, and memoise. Fibonacci recursion "
            "without memoisation takes O(phi^n) calls; with memoisation it takes O(n) states, "
            "each computed once. The length of a longest common subsequence follows the "
            "recurrence of comparing the last characters: if they match take one plus the "
            "diagonal, otherwise take the better of the two neighbours.\n\n"
            "Greedy algorithms make the locally best choice and never revisit it. They are "
            "dramatically faster, usually O(n log n), but correct only when a proof shows the "
            "local choice is safe. Activity selection, Huffman coding and Kruskal's algorithm "
            "are greedy; shortest path is not, which is exactly why Dijkstra needs a priority "
            "queue.\n\n"
            "Dynamic programming also underpins the ranking in this project: term weights, "
            "document frequencies and PageRank are all states that would otherwise be recomputed "
            "for every query. Cache them once and each query becomes a cheap lookup."
        ),
    },
    {
        "slug": "web-development-fundamentals",
        "title": "Web Development Fundamentals: The Request-Response Cycle",
        "category": "Web Development",
        "author": "A. D'Souza",
        "url": "nexasearch://web-development-fundamentals",
        "keywords": "web development, http, browser, server, cookies, session, caching",
        "content": (
            "The web is a system of clients and servers exchanging requests and responses over "
            "HTTP.\n\n"
            "HTTP is stateless: each request stands alone, which keeps components independent "
            "but forces state onto the client. Cookies and server sessions are the two "
            "solutions. A cookie is a small token sent with every request to a domain; session "
            "state stays on the server and only the identifier travels. Token-based APIs use a "
            "signed and time-limited token instead, which scales better across regions.\n\n"
            "A response carries status codes, headers and a body. Caching is the biggest "
            "performance lever: cache-control and expiry headers tell shared caches and browsers "
            "what they may reuse, and an entity tag lets a client revalidate cheaply instead of "
            "re-downloading.\n\n"
            "Statelessness and caching are in tension, since caching a personalised response "
            "would leak it. The resolution is to cache the shared part and vary the private "
            "part.\n\n"
            "The same origin policy restricts scripts on one origin from reading another. CORS "
            "lets a server opt in explicitly, which is why a well-configured API declares which "
            "origins may read its responses. Content security policy restricts what a page may "
            "load and execute, which limits the damage from an injected script.\n\n"
            "Web performance is measured with metrics such as largest contentful paint and "
            "interaction to next paint, and improved by minimising blocking resources, deferring "
            "scripts and caching aggressively."
        ),
    },
    {
        "slug": "html-css-layout",
        "title": "HTML Semantics and Modern CSS Layout",
        "category": "Web Development",
        "author": "A. D'Souza",
        "url": "nexasearch://html-css-layout",
        "keywords": "html, css, flexbox, grid, semantic markup, responsive design, accessibility",
        "content": (
            "Semantic markup describes what content is rather than how it looks, so that "
            "assistive technology, search engines and future redesigns all benefit. A page should "
            "use headings in order, landmark elements for regions, lists for collections and "
            "buttons for actions.\n\n"
            "The box model is the mental model for layout: every element is a rectangle with "
            "content, padding, border and margin, and the box-sizing property decides whether "
            "padding and border are inside the declared size.\n\n"
            "Before flexbox and grid, page layout was built with floats and absolute positioning, "
            "which meant fighting the document flow. Flexbox distributes space along one axis and "
            "aligns items on the cross axis, which makes it the right tool for components, toolbars "
            "and navigation. Grid defines two-dimensional tracks, which makes it the right tool "
            "for page-level layout and card grids. Using grid for the page and flexbox inside "
            "components is the common and sound combination.\n\n"
            "Responsive design adapts to the viewport using relative units, flexible breakpoints "
            "and content-driven queries rather than device widths.\n\n"
            "Accessibility is not optional: colour contrast, visible focus indicators, keyboard "
            "operability and descriptive alternative text are what make a page usable for "
            "everyone. The dark and light themes in this application both meet the contrast "
            "requirements for the same reason."
        ),
    },
    {
        "slug": "javascript-core",
        "title": "JavaScript Core: Values, Scope and the Event Loop",
        "category": "Web Development",
        "author": "A. D'Souza",
        "url": "nexasearch://javascript-core",
        "keywords": "javascript, event loop, closures, promises, prototype, single threaded",
        "content": (
            "JavaScript is single threaded with asynchronous callbacks, which is the source of "
            "both its simplicity and its characteristic bugs.\n\n"
            "Values have eight types, and objects are reference values with a prototype chain. "
            "Property lookup walks the chain, which is why a missing property read is undefined "
            "rather than an error, and why assigning a new property to a plain object is safe "
            "while traversing a hostile prototype chain is not.\n\n"
            "Scope is lexical, determined by where code is written rather than where it runs. A "
            "closure is a function plus the variables it captured when it was created, which is "
            "why a callback still sees the correct loop variable when the loop has finished.\n\n"
            "The event loop has one call stack, one microtask queue for promise callbacks, and a "
            "macrotask queue for timers and events. After the current task and all microtasks "
            "complete, the next macrotask runs. This is why a resolved promise callback runs "
            "before a setTimeout of zero, and why a long synchronous loop blocks the whole page.\n\n"
            "Promises represent a future value with pending, fulfilled and rejected states, and "
            "combinators such as all, race and any express concurrency. Async functions are "
            "syntax over promises. Timers are minimum delays, not guarantees."
        ),
    },
    {
        "slug": "rest-apis",
        "title": "REST API Design and Error Contracts",
        "category": "Web Development",
        "author": "A. D'Souza",
        "url": "nexasearch://rest-apis",
        "keywords": "rest api, json, http verbs, pagination, idempotency, rate limiting, error handling",
        "content": (
            "REST organises a system around resources with URLs that name them and HTTP methods "
            "that say what to do. GET is safe and idempotent, so it may be cached and retried. "
            "PUT and DELETE are idempotent. POST is neither and must not be retried blindly.\n\n"
            "Status codes form a contract: 200 for a successful read, 201 with a location header "
            "for a created resource, 204 for success with no body, 400 for a malformed request, "
            "401 when unauthenticated, 403 when authenticated but not permitted, 404 when "
            "absent, 409 on a conflicting state and 429 when rate limited. A 200 with an error "
            "body breaks every client that relies on the status.\n\n"
            "Large collections must paginate, with a cursor for stable traversal and an offset "
            "for jumping to a page.\n\n"
            "Idempotency keys make unsafe operations safe to retry: the server stores the key and "
            "replays the original result. Rate limits protect the service, and the contract "
            "should expose the limit, the remaining allowance and when it resets.\n\n"
            "Input validation belongs at the boundary, and the error response should say which "
            "field failed and why, without leaking internals. This project validates every "
            "query, document and algorithm parameter at the route layer and returns structured "
            "errors rather than stack traces."
        ),
    },
    {
        "slug": "java-fundamentals",
        "title": "Java Fundamentals: Objects, Types and the Garbage Collector",
        "category": "Java",
        "author": "H. Yamada",
        "url": "nexasearch://java-fundamentals",
        "keywords": "java, jvm, object oriented, type system, garbage collection, jit",
        "content": (
            "Java compiles source code to bytecode that runs on any Java virtual machine, which is "
            "where the language's portability comes from. The JIT compiler inside the JVM then "
            "compiles hot methods to native code at runtime, so performance depends on how well "
            "the JIT can profile the program.\n\n"
            "The type system is static and nominal: a variable's type is declared and enforced at "
            "compile time, and code cannot reinterpret a value as an unrelated type. Widening "
            "conversions are implicit, narrowing ones need an explicit cast, and autoboxing "
            "converts between primitives and their wrapper objects.\n\n"
            "Everything with an identity lives on the heap and is managed by a garbage collector; "
            "primitives and references live on the stack. The collector traces reachable objects "
            "from roots and reclaims the rest. Collecting unreachable objects is the easy part; "
            "collecting reachable ones that are no longer used is the hard part, and it is the "
            "job of reference counting in managed languages and escape analysis in the compiler.\n\n"
            "Equality has two forms. Reference identity is compared with the identity operator. "
            "Logical equality is compared with equals and must be implemented deliberately, "
            "especially when objects are used as keys in a hash-based structure.\n\n"
            "Checked exceptions are part of the language contract: the compiler forces the caller "
            "to handle or declare a checked exception, which makes failure paths visible in the "
            "signature."
        ),
    },
    {
        "slug": "java-collections",
        "title": "Java Collections: Interfaces, Complexity and Trade-offs",
        "category": "Java",
        "author": "H. Yamada",
        "url": "nexasearch://java-collections",
        "keywords": "java collections, arraylist, linkedlist, hashmap, treeset, complexity, iterator",
        "content": (
            "The collections framework separates interface from implementation, so code can depend "
            "on a list without depending on the concrete list.\n\n"
            "The random access list implementation is backed by an array. Getting an element is "
            "O(1); inserting in the middle is O(n) because everything after it shifts. Its cost "
            "per element is lower than the linked implementation, which is why the linked list is "
            "almost never faster in practice despite O(1) insertion after a node is located.\n\n"
            "Hash-based maps offer O(1) average get, put and remove, with the same caveat as any "
            "hash table: a poor hash function or an excessive load factor degrades the average "
            "toward O(n), and treeifying a collided bucket restores O(log n) at the cost of extra "
            "time and space. The map must also be treated as unordered; iteration order is a "
            "detail of the current bucket layout.\n\n"
            "Sorted collections give O(log n) operations and O(n) ordered traversal, implemented "
            "with a balanced tree whose comparisons are O(log n) when the comparator is "
            "expensive, so the comparator should be cheap and consistent.\n\n"
            "Iterators are the safe traversal mechanism: they provide fail-fast behaviour when the "
            "collection is modified during iteration, which surfaces a bug rather than silently "
            "skipping elements.\n\n"
            "These are exactly the trade-offs implemented by hand in the project's own trie and "
            "hash table, described in [[searching-algorithms]]."
        ),
    },
    {
        "slug": "python-fundamentals",
        "title": "Python Fundamentals: Objects, Iteration and Complexity",
        "category": "Python",
        "author": "J. Whitfield",
        "url": "nexasearch://python-fundamentals",
        "keywords": "python, list, dictionary, iteration, generators, comprehension, garbage collection",
        "content": (
            "Python is dynamically typed and garbage collected, with everything being an object "
            "and every object having a type and an identity.\n\n"
            "The built-in containers each have a deliberate complexity. Appending to a list is "
            "amortised O(1). Indexing and slicing are O(1) at the start and O(n) at the end of "
            "a slice, so avoid s[1:] in a loop. Looking up a dictionary key is O(1) average with "
            "the same collision caveat as any hash table, but deletion never shifts the array, "
            "which is why iteration order is stable. Sets behave like dictionaries without "
            "values. Tuples are immutable, hashable and therefore usable as dictionary keys.\n\n"
            "Dictionaries preserve insertion order, which makes them the tool for ordered "
            "aggregation, counting with a counter-like pattern, and grouping.\n\n"
            "Iteration is the core abstraction. A generator yields values lazily, so a pipeline "
            "over a large source uses constant memory. A list comprehension builds a list eagerly "
            "and is faster than an explicit loop because the bytecode avoids repeated attribute "
            "lookup. Generator expressions do the same lazily.\n\n"
            "Memory behaviour follows from this: a comprehension that accumulates is O(n) space, "
            "while a generator pipeline is O(1) plus whatever the consumer keeps.\n\n"
            "This project is written in Python with every data structure for the search engine "
            "built by hand precisely because the built-ins would hide the algorithms."
        ),
    },
    {
        "slug": "python-data-structures",
        "title": "Python Data Structures: Choosing the Right Container",
        "category": "Python",
        "author": "J. Whitfield",
        "url": "nexasearch://python-data-structures",
        "keywords": "python data structures, deque, heapq, bisect, defaultdict, counter, namedtuple",
        "content": (
            "Choosing a container in Python is a complexity decision.\n\n"
            "The list is the general sequence with O(1) amortised append at the end, but adding "
            "or removing at the front is O(n) because elements shift. The double-ended queue is "
            "the correct container for a queue or a sliding window, with O(1) operations at both "
            "ends.\n\n"
            "A priority queue keeps the smallest element available in O(1) and pops in O(log n), "
            "which is what the shortest-path algorithm needs. Two implementation details matter: "
            "comparison of tuples falls back to the second element when the first ties, which "
            "makes counter-intuitive results appear if the second element is not of the same "
            "type; and lazy deletion means stale entries stay in the heap until popped, so the "
            "algorithm must check whether an entry is out of date.\n\n"
            "Bisection finds an insertion point in a sorted sequence in O(log n) comparisons, "
            "but its C implementation needs only O(log n) comparisons too, so no custom binary "
            "search is needed for speed alone. This project implements binary search by hand "
            "anyway, because the algorithm is the subject.\n\n"
            "A dictionary with a default factory avoids repeated membership checks, and a "
            "counting helper removes the most common counting loop.\n\n"
            "Named tuples and small classes give records with readable attribute access, which "
            "keeps algorithms readable instead of dictionary indexing."
        ),
    },
    {
        "slug": "devops-fundamentals",
        "title": "DevOps Fundamentals: Culture, Automation and Feedback Loops",
        "category": "DevOps",
        "author": "P. Sandhu",
        "url": "nexasearch://devops-fundamentals",
        "keywords": "devops, automation, continuous delivery, feedback loop, toil, infrastructure as code",
        "content": (
            "DevOps is the set of practices that shorten the time between writing code and getting "
            "useful feedback from users, while keeping the system releasable.\n\n"
            "The core mechanism is a feedback loop. Without automation, feedback travels by "
            "ticket and email and takes days, by which time it is about a different version of "
            "the system. With automation the loop is minutes, and that frequency is what makes "
            "small batches safe.\n\n"
            "Continuous integration means every change is built and tested on a shared branch. "
            "Continuous delivery means a build can be released at any time, and continuous "
            "deployment means releasing is automatic.\n\n"
            "Infrastructure as code declares servers, networks and configuration in version "
            "control, so environment changes are reviewed like code and drift becomes visible. "
            "Without it, a deployment is a ritual performed differently by each engineer.\n\n"
            "Toil is manual, repetitive work that scales linearly with load. Reducing toil is a "
            "measurable engineering goal, and observability is what tells you where it is.\n\n"
            "Shared responsibility between development and operations is a design constraint: if "
            "the team that writes a service also runs it, the design has to be operable."
        ),
    },
    {
        "slug": "continuous-integration",
        "title": "Continuous Integration and Deployment Pipelines",
        "category": "DevOps",
        "author": "P. Sandhu",
        "url": "nexasearch://continuous-integration",
        "keywords": "continuous integration, pipeline, unit testing, build automation, canary release, rollback",
        "content": (
            "A pipeline turns a commit into a running artifact through fixed stages: build, unit "
            "test, static analysis, integration test, package, deploy to staging, verify, and "
            "promote to production.\n\n"
            "Builds must be reproducible, which means pinning dependency versions, not depending "
            "on the state of a developer machine, and building from a clean environment.\n\n"
            "Testing at different stages costs different amounts and catches different classes of "
            "defect. Unit tests are fast and numerous, integration tests exercise real "
            "dependencies, and end-to-end tests are slow but cover user-visible paths. Most "
            "defects should be caught by the cheap layers, because a defect found in an "
            "end-to-end test has already consumed the whole pipeline.\n\n"
            "A pipeline must fail fast, and the signal must be visible. Flaky tests are worse "
            "than missing tests because they teach the team to ignore red builds.\n\n"
            "Deployment strategies trade blast radius against speed. Recreate stops everything, "
            "which is unacceptable at scale. Rolling updates keep old and new versions running "
            "together, so both schemas must be compatible during the overlap. Blue-green "
            "switches instantly but doubles capacity. Canary releases send a small fraction of "
            "traffic to the new version, which is the safest and needs the best observability.\n\n"
            "Rollback must be automatic, rehearsed, and faster than debugging. A release nobody "
            "can undo is a release nobody should ship."
        ),
    },
    {
        "slug": "containers-docker",
        "title": "Docker and Container Image Management",
        "category": "DevOps",
        "author": "P. Sandhu",
        "url": "nexasearch://containers-docker",
        "keywords": "docker, container image, layer, registry, compose, entrypoint, security",
        "content": (
            "An image is a set of layers; a container is a running instance with a writable top "
            "layer. Each layer stores only the files that differ from the layer below, so "
            "unchanged files are shared between images.\n\n"
            "Because layers are content-addressed, build cache depends on instruction order. "
            "Copying the dependency manifest before the source, and installing dependencies "
            "immediately, means a source-only change does not invalidate the dependency layer. "
            "Getting this wrong is the most common cause of slow builds.\n\n"
            "Writing layers in the right order also produces smaller, safer images. Combining "
            "package installation and cleanup in one layer prevents the caches and lists of the "
            "package manager from surviving in a later layer, since deleted files still occupy "
            "space in the layer where they were created.\n\n"
            "Multi-stage builds compile in a full builder image and copy only the artefact into a "
            "minimal runtime image, so compilers and headers never reach production.\n\n"
            "The entrypoint and command form the process contract. The main process should run "
            "in the foreground and receive signals, otherwise graceful shutdown is impossible.\n\n"
            "Images run as root by default, which is unnecessary and dangerous. Running as a "
            "non-root user, scanning images for known vulnerabilities in a registry, and pinning "
            "base images by digest are all part of a reasonable supply-chain policy.\n\n"
            "A compose file describes several containers that must work together for local "
            "development, which is how the database in this project is started locally."
        ),
    },
]
