"""Sample corpus, part 2 of 3 - Cybersecurity, Computer Networks,
Operating Systems and Databases (16 original educational documents).
"""

ARTICLES: list[dict] = [
    {
        "slug": "cybersecurity-fundamentals",
        "title": "Cybersecurity Fundamentals and the CIA Triad",
        "category": "Cybersecurity",
        "author": "K. Osei",
        "url": "nexasearch://cybersecurity-fundamentals",
        "keywords": "cybersecurity, cia triad, authentication, least privilege, risk assessment",
        "content": (
            "Security engineering is the practice of making a system accept the right requests "
            "and reject the rest, while keeping that true as the system changes.\n\n"
            "The CIA triad is the traditional summary: confidentiality, integrity and "
            "availability. Confidentiality limits disclosure to authorised parties. Integrity "
            "means a message cannot be altered undetected. Availability means authorised users "
            "can reach the system when needed. A fourth property is increasingly treated as equal "
            "in status: authenticity, proving that a party really is who it claims to be.\n\n"
            "The core principle is least privilege: every component and account receives only "
            "the permissions it needs for the task it performs. Combined with defence in depth, "
            "where several independent controls must fail before an attack succeeds, and fail "
            "safely, where a control that rejects denies access rather than allowing it, this "
            "turns a single mistake into an incident rather than a breach.\n\n"
            "Authentication proves identity using something the user knows, something they have, "
            "or something they are. Each factor can be phished, stolen or coerced, which is why "
            "multi-factor authentication is recommended. Authorisation then decides what an "
            "authenticated identity may do.\n\n"
            "Risk assessment ranks assets by impact and likelihood, and the chosen control "
            "reduces the risk that matters. Absolute security does not exist; the goal is an "
            "acceptable residual risk, which must be accepted deliberately by an owner."
        ),
    },
    {
        "slug": "cryptography-basics",
        "title": "Applied Cryptography: Hashing, Symmetric and Asymmetric Keys",
        "category": "Cybersecurity",
        "author": "K. Osei",
        "url": "nexasearch://cryptography-basics",
        "keywords": "cryptography, hashing, sha256, symmetric encryption, aes, rsa, public key",
        "content": (
            "Cryptography provides confidentiality, integrity, authentication and "
            "non-repudiation. Three primitive families do the work.\n\n"
            "A cryptographic hash maps any input to a fixed-size digest and must be "
            "deterministic, fast to compute, preimage resistant, second-preimage resistant and "
            "collision resistant. SHA-256 produces 256 bits and is the usual default. Password "
            "storage does not use a plain hash: it uses a slow, salted, iterated key derivation "
            "function such as bcrypt, scrypt or Argon2, so that guessing is expensive and "
            "identical passwords produce different stored values.\n\n"
            "Symmetric encryption uses one shared key. AES in Galois counter mode is the modern "
            "default and runs at gigabytes per second, but both parties must hold the key, so "
            "distribution is the hard problem.\n\n"
            "Asymmetric encryption uses a key pair. The public key can be published; the private "
            "key is never shared. It solves key distribution and enables digital signatures, at "
            "the cost of being far slower. RSA and elliptic curve schemes such as ECDSA are in "
            "common use.\n\n"
            "In practice, protocols combine them: transport layer security establishes a shared "
            "symmetric session key with asymmetric key exchange and then encrypts bulk data "
            "symmetrically. Hashing is the same rolling-hash idea used by "
            "[[string-matching-algorithms]] in string matching, but designed against adversaries."
        ),
    },
    {
        "slug": "network-security-threats",
        "title": "Common Network Threats and Practical Defences",
        "category": "Cybersecurity",
        "author": "K. Osei",
        "url": "nexasearch://network-security-threats",
        "keywords": "network security, phishing, man in the middle, ddos, firewall, intrusion detection",
        "content": (
            "Threats are grouped by what the attacker wants and how they reach the target.\n\n"
            "Passive attacks observe without altering: eavesdropping on unencrypted traffic, "
            "sniffing on a shared medium, and traffic analysis that infers activity from timing "
            "and volume. Confidentiality is the target, and encryption with authenticated modes "
            "is the defence.\n\n"
            "Active attacks alter data or deny service. A man-in-the-middle relays traffic "
            "between two parties who believe they talk to each other; mutual authentication with "
            "certificates and pinning defeats it. Replay attacks reuse a captured message, "
            "defeated by nonces and sequence numbers. Denial of service floods a target so that "
            "legitimate traffic is starved, and is mitigated by rate limiting, anycast "
            "distribution and upstream scrubbing rather than by bandwidth alone.\n\n"
            "Social engineering targets people rather than machines. Phishing, pretexting and "
            "tailgating bypass technical controls entirely. Technical measures help by making "
            "phishing harder to automate: mail authentication records, hardware-backed "
            "multi-factor authentication and least privilege.\n\n"
            "Detection uses a firewall for permitted flows, an intrusion detection system for "
            "signatures and anomalies, and centralised logging for investigation. Defence is "
            "layered because any single control can fail; the network layer is described in "
            "[[tcp-ip-protocols]] and the host layer in [[operating-systems-concepts]]."
        ),
    },
    {
        "slug": "ethical-hacking",
        "title": "Ethical Hacking, Penetration Testing and Responsible Disclosure",
        "category": "Cybersecurity",
        "author": "K. Osei",
        "url": "nexasearch://ethical-hacking",
        "keywords": "ethical hacking, penetration testing, vulnerability assessment, responsible disclosure",
        "content": (
            "Penetration testing is an authorised attempt to break a system so the owner learns "
            "how before an adversary does. Legality rests entirely on written authorisation that "
            "names the systems, the dates and the testing methods.\n\n"
            "Testing is structured into phases: reconnaissance, scanning, gaining access, "
            "maintaining access, covering tracks, and reporting. Reconnaissance is open-source "
            "intelligence; scanning finds live hosts and services; the rest validate whether the "
            "defences actually work.\n\n"
            "A vulnerability assessment is broader and shallower: it enumerates and ranks known "
            "issues without necessarily exploiting them. A penetration test is narrower and "
            "deeper. Both end with a report that ranks findings by business impact, gives "
            "reproduction steps and remediation guidance, and avoids publishing exploit details "
            "for unpatched systems.\n\n"
            "Responsible disclosure coordinates with the vendor: report privately, allow a stated "
            "period for a fix, then disclose. Programmes now exist in most large vendors and "
            "often pay bounties, which turns a harmful act into a legitimate contribution.\n\n"
            "Ethical practice also includes scope discipline. Testing infrastructure you were "
            "not authorised to touch is a crime regardless of intent, and third-party services "
            "in scope of a contract may not be covered by a test authorisation at all."
        ),
    },
    {
        "slug": "computer-networks-basics",
        "title": "Computer Networks: Layers, Protocols and the Packet Life",
        "category": "Computer Networks",
        "author": "T. Banerjee",
        "url": "nexasearch://computer-networks-basics",
        "keywords": "computer networks, osi model, tcp ip, packet, bandwidth, latency, throughput",
        "content": (
            "A network lets machines exchange messages. The packet is the basic unit: a small "
            "header carrying addressing and control information, and a payload. Splitting data "
            "into packets lets many hosts share a link and lets routers forward each packet "
            "independently.\n\n"
            "The OSI model is a seven-layer reference: physical, data link, network, transport, "
            "session, presentation and application. Each layer uses the services of the layer "
            "below and offers a service to the layer above, so a change at one layer does not "
            "require rewriting the others. TCP/IP folds these into four or five practical layers.\n\n"
            "Addressing is hierarchical, which is why routers can scale: an address contains a "
            "network part that identifies where to send the packet and a host part that "
            "identifies the machine. Longest-prefix matching picks the most specific route.\n\n"
            "Performance has three distinct measures. Bandwidth is the maximum data rate of a "
            "link. Latency is the delay for one packet, itself a sum of propagation, "
            "transmission and queuing delay. Throughput is the rate of useful data actually "
            "delivered, which is always at most bandwidth and usually far less because of "
            "overhead, contention and retransmissions.\n\n"
            "Congestion control is the reason the internet works: hosts reduce their sending rate "
            "when the network signals congestion, trading throughput for fairness and stability."
        ),
    },
    {
        "slug": "tcp-ip-protocols",
        "title": "TCP and IP: Connection, Reliability and Routing",
        "category": "Computer Networks",
        "author": "T. Banerjee",
        "url": "nexasearch://tcp-ip-protocols",
        "keywords": "tcp, ip, three way handshake, congestion control, sequence numbers, routing",
        "content": (
            "The internet protocol is connectionless and best effort. It forwards packets "
            "independently and makes no promise about delivery, order or duplication, which keeps "
            "routers simple and fast. Reliability is added above it.\n\n"
            "The transmission control protocol provides a reliable byte stream on top of IP. It "
            "assigns sequence numbers so the receiver can detect loss and reorder, acknowledges "
            "received bytes, and retransmits what is missing. The connection is established by a "
            "three-way handshake: a request, an acknowledgement, and a final acknowledgement. "
            "Teardown is symmetric, since each side may close independently.\n\n"
            "The user datagram protocol provides no guarantees at all, which is appropriate for "
            "real-time media and for name resolution, where a retry is cheaper than a "
            "guarantee. QUIC runs on top of UDP and rebuilds the reliability features in user "
            "space, which allows connection migration and zero round-trip resumption.\n\n"
            "TCP flow control protects the receiver with a window; congestion control protects "
            "the network with a congestion window. Slow start doubles the window each round trip "
            "until loss occurs, then multiplicative decrease halves it, and modern variants such "
            "as CUBIC and BBR refine the response.\n\n"
            "Routing happens at the IP layer. Distance vector protocols such as RIP exchange "
            "whole distance tables and converge slowly; link state protocols such as OSPF build "
            "a map and run Dijkstra's algorithm over it, converging faster. That algorithm is "
            "covered in [[graph-algorithms]]."
        ),
    },
    {
        "slug": "dns-internet",
        "title": "DNS and How the Internet Finds Names",
        "category": "Computer Networks",
        "author": "T. Banerjee",
        "url": "nexasearch://dns-internet",
        "keywords": "dns, domain name, root servers, caching, ttl, dnssec",
        "content": (
            "The domain name system maps human-readable names to addresses. It is a distributed, "
            "hierarchical database, and it is the most used service on the internet.\n\n"
            "Names are structured right to left. The root is the empty label, then top-level "
            "domains, then second-level names. Resolvers walk down this tree: they ask a root "
            "server for the address of a name server for the top-level domain, then ask that "
            "server, and so on. Any of these responses may be answered from cache instead.\n\n"
            "Every record has a time to live, which bounds how long a cache may serve it. Short "
            "TTLs make changes propagate quickly but increase query volume. Propagation is in "
            "fact never immediate, which is why a cutover must be planned with an overlap period.\n\n"
            "Record types include address records, name-server records, mail-exchange records "
            "and canonical-name aliases. IPv6 adds a parallel record type for the newer address "
            "format.\n\n"
            "Security relies on two mechanisms. Transport layer security protects queries in "
            "flight. DNSSEC signs records end to end so a resolver can detect forgery, but it "
            "must be deployed at every level of the hierarchy to be useful, and it protects "
            "integrity rather than privacy.\n\n"
            "Caching is what makes the system scalable: without it every lookup would traverse "
            "the whole hierarchy. This is a direct application of memoisation, the same "
            "technique described in [[dynamic-programming]]."
        ),
    },
    {
        "slug": "network-performance",
        "title": "Measuring and Improving Network Performance",
        "category": "Computer Networks",
        "author": "T. Banerjee",
        "url": "nexasearch://network-performance",
        "keywords": "network performance, qos, latency, packet loss, jitter, throughput, load balancing",
        "content": (
            "Performance work begins with measurement. Round-trip time measures delay, "
            "packet-loss ratio measures reliability, jitter measures variation in arrival time, "
            "and goodput measures useful payload throughput after protocol overhead.\n\n"
            "The throughput-delay product is the number of bits that can be in flight in a link "
            "at once. It is the real capacity of a path, and it explains why a link with large "
            "bandwidth but long latency cannot transfer a large file quickly.\n\n"
            "Bottlenecks are found by measurement, not assumption: interface counters, queue "
            "depth, retransmission rate and latency percentiles across each hop. A single "
            "congested hop makes the whole path slow.\n\n"
            "Quality of service lets a network prioritise: latency-sensitive traffic such as voice "
            "is shaped and policed before bulk transfer. Shaping smooths bursts with a queue, "
            "policing enforces a contract by dropping or marking excess.\n\n"
            "Common remedies are content delivery networks for proximity, compression for "
            "bandwidth, caching for repeated requests, connection reuse to avoid repeated "
            "handshakes, and load balancing to spread demand. The trade-off is always between "
            "latency and consistency, and between cost and redundancy."
        ),
    },
    {
        "slug": "operating-systems-concepts",
        "title": "Operating System Concepts: Virtualisation and Abstraction",
        "category": "Operating Systems",
        "author": "L. Moreau",
        "url": "nexasearch://operating-systems-concepts",
        "keywords": "operating system, kernel, system call, virtual memory, abstraction, syscall",
        "content": (
            "An operating system is the layer that turns hardware into an environment programs "
            "can use. It does this by hiding hardware detail behind abstractions and by "
            "arbitrating access to shared resources.\n\n"
            "A process is an execution context with its own address space, while a thread is a "
            "schedulable stream of instructions inside a process. Threads of one process share "
            "memory, so they must synchronise explicitly; processes are isolated, so they "
            "communicate slowly through the operating system.\n\n"
            "The kernel runs in privileged mode and exposes system calls as the only controlled "
            "entry point. User code cannot execute a privileged instruction or touch another "
            "process memory, which is the hardware-assisted basis of protection between "
            "processes and between users.\n\n"
            "Virtualisation lets one physical machine host many isolated environments, each with "
            "its own kernel view. Container runtimes use operating-system primitives, namespaces "
            "and control groups, instead of a hypervisor, so they start much faster but share "
            "the host kernel, as described in [[containers-in-cloud]].\n\n"
            "An operating system is fundamentally a resource scheduler and a protection "
            "mechanism. Scheduling policies are compared in [[process-scheduling]], memory "
            "management in [[memory-management]] and naming in [[file-systems]]."
        ),
    },
    {
        "slug": "process-scheduling",
        "title": "Process Scheduling Policies and Deadlocks",
        "category": "Operating Systems",
        "author": "L. Moreau",
        "url": "nexasearch://process-scheduling",
        "keywords": "process scheduling, round robin, priority, first fit, deadlock, banker's algorithm",
        "content": (
            "The scheduler decides which ready process runs next, and its objective changes with "
            "the workload: throughput for batch, response time for interactive, fairness for "
            "servers.\n\n"
            "First come first served is simple and fair on average but suffers the convoy effect, "
            "where a long job blocks everyone. Shortest job first provably minimises average "
            "waiting time, but it needs to know runtimes in advance and starves long jobs. "
            "Shortest remaining time is preemptive and optimal for average waiting. "
            "Round robin gives every process a slice and adds a context switch every slice, so "
            "its cost is O(n) per slice for n runnable processes.\n\n"
            "Priority scheduling serves the highest priority first, with ageing to prevent "
            "starvation. Multilevel feedback queues approximate the behaviour of shortest job "
            "first without knowing runtimes by demoting processes that use their slice.\n\n"
            "Deadlock requires mutual exclusion, hold and wait, no preemption and circular wait. "
            "Prevention breaks one condition directly, which usually costs concurrency. "
            "Detection runs an algorithm to discover whether a deadlock exists; the banker's "
            "algorithm does this by simulating all future requests. Avoidance, which is the "
            "banker's approach, admits a request only if a safe sequence remains possible."
        ),
    },
    {
        "slug": "memory-management",
        "title": "Memory Management: Paging, Segmentation and Replacement",
        "category": "Operating Systems",
        "author": "L. Moreau",
        "url": "nexasearch://memory-management",
        "keywords": "memory management, paging, page table, tlb, page fault, virtual memory, lru",
        "content": (
            "Each process sees a contiguous virtual address space that the operating system maps "
            "to physical frames. Paging splits both spaces into fixed-size pages and frames and "
            "keeps them in a page table, which removes the need for contiguous allocation.\n\n"
            "A page fault occurs when a referenced page is not resident. The operating system "
            "loads it from disk, replacing another page if necessary. If no free frame exists it "
            "must evict. The translation lookaside buffer caches recent page table entries in "
            "hardware, so a miss there costs a memory access rather than a full page table walk.\n\n"
            "Page replacement policies differ sharply. Optimal replacement evicts the page not "
            "used for the longest future time, which is unimplementable but a useful bound. "
            "Least recently used approximates it and is O(1) to record, though true LRU needs a "
            "hardware counter or a stack, and suffers from the sequential-scan pathology where "
            "one pass evicts everything another pass needs. Clock approximates LRU with a single "
            "sweep bit, which is cheap and behaves well.\n\n"
            "Thrashing happens when a process is given too few frames and spends more time "
            "paging than working, which costs more than not running. The working set model and "
            "page-fault frequency control both respond.\n\n"
            "Page size is a genuine trade-off: large pages cut table entries and overhead, small "
            "pages waste less memory on partially used pages."
        ),
    },
    {
        "slug": "file-systems",
        "title": "File Systems: Allocation, Indexing and Consistency",
        "category": "Operating Systems",
        "author": "L. Moreau",
        "url": "nexasearch://file-systems",
        "keywords": "file system, inode, allocation, journaling, directory, consistency, fsck",
        "content": (
            "A file system maps names to byte ranges on a persistent device and makes the "
            "mapping survive crashes.\n\n"
            "Allocation decides where file data lives. Contiguous allocation is fast to read and "
            "simple, but external fragmentation makes it impractical for general use. Linked "
            "allocation removes fragmentation but makes random access proportional to the number "
            "of links. Extent allocation, which stores runs of contiguous blocks, is the modern "
            "compromise and is what ext4 and modern databases use.\n\n"
            "Metadata is stored in structures such as inodes and directory entries. An inode "
            "holds attributes and block pointers, and directory entries map names to inodes. "
            "Indexed allocation stores a tree of block pointers so a lookup is proportional to "
            "the logarithm of the file size rather than its length.\n\n"
            "A write-ahead journal records intended operations before they happen. After a crash "
            "the system replays or discards the journal, which converts an arbitrary corruption "
            "into a bounded rollback. Consistency is what makes the difference between a "
            "database feature and a file system detail.\n\n"
            "Recovery still matters when the journal itself is lost, which is why file systems "
            "ship consistency checkers that walk the structures looking for damage."
        ),
    },
    {
        "slug": "database-fundamentals",
        "title": "Relational Database Fundamentals and ACID Transactions",
        "category": "Databases",
        "author": "V. Aleksyev",
        "url": "nexasearch://database-fundamentals",
        "keywords": "relational database, sql, acid, transaction, isolation, durability",
        "content": (
            "A database management system stores structured data and answers queries about it. The "
            "relational model represents data as tables of tuples over a fixed schema, and "
            "queries are expressed in a declarative language, SQL, where the system chooses the "
            "execution plan.\n\n"
            "A transaction groups operations into one all-or-nothing unit. ACID names the four "
            "guarantees. Atomicity means all statements commit or none do. Consistency means the "
            "constraints declared in the schema hold after every transaction. Isolation means "
            "concurrent transactions do not see each other's partial work. Durability means "
            "committed data survives a crash.\n\n"
            "Isolation levels are a deliberate trade-off. Read uncommitted permits dirty reads. "
            "Read committed forbids them but still allows non-repeatable reads. Repeatable read "
            "prevents those but may allow phantom rows from concurrent inserts. Serializable "
            "prevents all of them and costs the most, usually through lock holding to the end "
            "of the transaction.\n\n"
            "Recovery uses a write-ahead log and checkpoints. After a crash the log replays "
            "committed work and undoes uncommitted work, so durability and atomicity survive "
            "without rewriting whole tables."
        ),
    },
    {
        "slug": "relational-modeling",
        "title": "Normalisation, Keys and Referential Integrity",
        "category": "Databases",
        "author": "V. Aleksyev",
        "url": "nexasearch://relational-modeling",
        "keywords": "normalisation, first normal form, primary key, foreign key, referential integrity, joins",
        "content": (
            "Normalisation organises data to remove redundancy and therefore to remove anomalies. "
            "An insertion anomaly loses data when a fact about a subject is stored only in one "
            "of its rows. An update anomaly requires changing many rows to change one fact. A "
            "deletion anomaly erases a fact by deleting an unrelated row.\n\n"
            "First normal form requires atomic attribute values. Second normal form removes "
            "partial dependency on a composite key. Third normal form removes transitive "
            "dependency of a non-key attribute on the key. Boyce-Codd normal form and fourth "
            "normal form handle the remaining cases involving overlapping candidate keys and "
            "independent multivalued dependencies.\n\n"
            "Each normalisation step is a join, so applying one costs query performance at write "
            "time. Deliberate denormalisation is therefore a normal engineering decision for "
            "read-heavy systems, provided the redundancy is protected by triggers or "
            "application logic.\n\n"
            "Keys give identity. A primary key is unique and non-null. A surrogate key is an "
            "artificial identifier that is stable, while a natural key is derived from the data "
            "itself and is meaningful but can change. Foreign keys express relationships, and "
            "referential integrity guarantees that a referenced row exists, with cascading "
            "actions deciding what happens on delete or update.\n\n"
            "Joins combine tables, and their order and algorithm matter enormously, which leads "
            "to [[indexing-databases]]."
        ),
    },
    {
        "slug": "indexing-databases",
        "title": "Database Indexing: B-Trees, Hash Indexes and Query Plans",
        "category": "Databases",
        "author": "V. Aleksyev",
        "url": "nexasearch://indexing-databases",
        "keywords": "database index, b-tree, binary search, hash index, query plan, composite index",
        "content": (
            "An index is an auxiliary structure that trades write cost and storage for read "
            "speed. It should only exist to serve a query someone actually runs.\n\n"
            "A B-tree keeps keys sorted and the tree balanced, so each node is nearly full and "
            "every leaf is at the same depth. That gives a fixed small number of page reads per "
            "lookup, which is what matters when a page read is a disk seek. The binary search "
            "at the heart of each node is the algorithm in [[searching-algorithms]].\n\n"
            "A hash index maps keys directly to row locations, giving constant-time equality "
            "lookups but no ordering, so it cannot serve range queries or ordered output. It "
            "also degrades under collisions, which is the same trade-off the hash table makes in "
            "[[searching-algorithms]].\n\n"
            "Composite indexes are ordered left to right, so a composite index on region then "
            "date can serve a query filtering both, or filtering region alone, but not filtering "
            "date alone. Covering indexes include the columns the query needs so the lookup never "
            "visits the table itself.\n\n"
            "The query planner chooses between them using statistics, so stale statistics produce "
            "bad plans. Partial and expression indexes extend the idea to subsets and computed "
            "columns. Write amplification is the cost of maintaining an index on every insert."
        ),
    },
    {
        "slug": "nosql-databases",
        "title": "NoSQL Stores and the CAP Theorem",
        "category": "Databases",
        "author": "V. Aleksyev",
        "url": "nexasearch://nosql-databases",
        "keywords": "nosql, cap theorem, eventual consistency, key value store, document store",
        "content": (
            "NoSQL is a family of stores that abandon the fixed relational schema in exchange for "
            "horizontal scale and flexible access patterns.\n\n"
            "Key-value stores map a key to an opaque value. They are the simplest and fastest, "
            "but the database cannot query anything it does not know how to key.\n\n"
            "Document stores keep self-describing documents and index their fields. Flexibility "
            "comes from avoiding schema migration for new attributes, at the cost of weaker "
            "cross-document guarantees.\n\n"
            "Wide-column and column-family stores group columns per row family so sparse data is "
            "cheap. They scale writes by partitioning and are used for very large time-series or "
            "event tables. Graph stores keep relationships as first-class edges, which is the "
            "right model when traversal is the main query; the algorithms involved are described "
            "in [[graph-algorithms]].\n\n"
            "The CAP theorem says a distributed store cannot simultaneously guarantee strong "
            "consistency, availability under partition, and partition tolerance. Since real "
            "networks partition, the choice is consistency or availability. Eventual consistency "
            "buys availability and means replicas converge without a fixed bound on delay, so "
            "reads may be stale. Choosing the trade-off per operation is more realistic than "
            "choosing it per system."
        ),
    },
]
