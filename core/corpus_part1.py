"""Sample corpus, part 1 of 3 - Artificial Intelligence, Machine Learning,
Data Science and Cloud Computing (17 original educational documents).

All content is written from scratch for this project; nothing is copied from
a copyrighted source.  Cross-references use ``[[slug]]`` markers, which the
graph builder turns into directed edges for BFS / DFS / Dijkstra / PageRank.
"""

ARTICLES: list[dict] = [
    {
        "slug": "ai-foundations",
        "title": "Foundations of Artificial Intelligence",
        "category": "Artificial Intelligence",
        "author": "Dr. A. Raghavan",
        "url": "nexasearch://ai-foundations",
        "keywords": "artificial intelligence, ai definition, intelligent agents, rational agent, search problem",
        "content": (
            "Artificial Intelligence is the branch of computer science concerned with building "
            "systems that perform tasks which normally require human intelligence. The classical "
            "textbook definition of AI is the study of how to make computers do things that, "
            "if done by a human, would be called intelligent.\n\n"
            "A useful organising idea is the rational agent: an agent that perceives its "
            "environment through sensors and acts through actuators so as to maximise a measure "
            "of performance. Every AI technique is one particular strategy for implementing "
            "that agent. A search-based agent explores a state space, a knowledge-based agent "
            "stores facts and rules, and a learning agent improves from data.\n\n"
            "AI is usually split into symbolic approaches and connectionist approaches. "
            "Symbolic systems reason over explicit representations, which makes their "
            "decisions explainable but their knowledge hard to acquire. Connectionist systems, "
            "that is neural networks, learn distributed representations from examples, which "
            "makes them powerful but opaque.\n\n"
            "The problems studied in AI recur throughout computer science. Search and "
            "optimisation appear in [[searching-algorithms]], planning and reasoning reuse "
            "graph traversal techniques from [[graph-algorithms]], and the evaluation of "
            "learned systems depends on the statistical tools described in "
            "[[statistics-for-data-science]]. Machine learning supplies the learning half of "
            "the intelligent agent; see [[ml-supervised-learning]]."
        ),
    },
    {
        "slug": "ai-history-philosophy",
        "title": "A Short History and Philosophy of AI",
        "category": "Artificial Intelligence",
        "author": "Dr. A. Raghavan",
        "url": "nexasearch://ai-history-philosophy",
        "keywords": "ai history, turing test, symbolic ai, expert systems, ai winters",
        "content": (
            "The idea of mechanical reasoning is old, but the field named artificial intelligence "
            "began in 1956, when researchers proposed that every aspect of learning or any other "
            "feature of intelligence could in principle be described precisely enough for a "
            "machine to simulate it.\n\n"
            "The symbolic era dominated the 1960s and 1970s. Early programs solved small "
            "problems and then failed on realistic ones, an effect later nicknamed the AI winter. "
            "Expert systems in the 1980s worked in narrow domains such as medical diagnosis and "
            "computer configuration, but they were brittle: they could not learn, and every new "
            "case needed a new rule.\n\n"
            "In 1950 Alan Turing proposed the imitation game, now called the Turing test, as an "
            "operational answer to the question can machines think. The test is behavioural, not "
            "theoretical, which is why the debate about it is still open.\n\n"
            "Connectionism revived in the 1980s with backpropagation for multilayer perceptrons. "
            "Three things changed later: more data, more compute, and better algorithms such as "
            "convolutional and attention architectures. Together they moved the field from "
            "hand-written rules to statistical learning, which is exactly the shift described in "
            "[[ml-deep-learning]] and formalised in [[ml-supervised-learning]].\n\n"
            "The philosophical split between strong and weak AI still shapes expectations: weak "
            "AI claims a system can do one task well, strong AI claims general human-like "
            "understanding."
        ),
    },
    {
        "slug": "ai-neural-networks-basics",
        "title": "How Neural Networks Learn: A First Model",
        "category": "Artificial Intelligence",
        "author": "S. Kulkarni",
        "url": "nexasearch://ai-neural-networks-basics",
        "keywords": "neural network, perceptron, activation function, backpropagation, gradient descent",
        "content": (
            "A neural network is a stack of layers of simple units. Each unit computes a weighted "
            "sum of its inputs, adds a bias, and passes the result through a non-linear "
            "activation function such as the sigmoid, the hyperbolic tangent, or the rectified "
            "linear unit.\n\n"
            "The 1958 perceptron is the smallest example. For inputs x with weights w and bias b, "
            "the output is the sign of the dot product. The perceptron learning rule adjusts the "
            "weights towards the target whenever it misclassifies. It converges only if the data "
            "is linearly separable, a limitation discovered by Minsky and Papert that stalled "
            "connectionism for years.\n\n"
            "Deep networks remove that limitation by stacking layers, so that a linear decision "
            "boundary in the input space becomes a highly non-linear boundary after composition. "
            "Learning proceeds by gradient descent: compute the loss, differentiate it with "
            "respect to every weight using the chain rule backwards through the layers, and move "
            "each weight opposite the gradient. This procedure is called backpropagation.\n\n"
            "The cost of a single training step is proportional to the number of weights, and the "
            "number of steps needed is roughly proportional to the inverse of the learning rate, "
            "so training is computationally expensive. Modern practice uses adaptive learning "
            "rates, mini-batches and regularisation. See [[ml-deep-learning]] for architectures "
            "and [[ml-model-evaluation]] for measuring the result."
        ),
    },
    {
        "slug": "ai-ethics",
        "title": "Ethics, Bias and Accountability in AI Systems",
        "category": "Artificial Intelligence",
        "author": "Dr. M. Fernandes",
        "url": "nexasearch://ai-ethics",
        "keywords": "ai ethics, algorithmic bias, fairness, explainability, accountability",
        "content": (
            "A model learns whatever signal is present in its training data. If historical "
            "decisions were unfair, the model reproduces those unfairness patterns at scale, "
            "and it does so without anyone writing the rule explicitly.\n\n"
            "Two bias mechanisms dominate. Sampling bias occurs when the training set does not "
            "represent the deployment population. Measurement bias occurs when a proxy variable "
            "stands in for the real thing. Both reduce coverage for minority groups, and the "
            "usual accuracy metric hides this because overall accuracy is dominated by the "
            "majority class.\n\n"
            "Common fairness definitions are mutually incompatible in general. Demographic parity "
            "requires equal positive rates across groups. Equalised odds requires equal true "
            "positive and false positive rates. A system can satisfy one and violate the other "
            "unless the base rates are equal, which is the theorem behind the impossibility "
            "result. Choosing a definition is therefore a policy decision, not a technical one.\n\n"
            "Accountability requires more than accuracy. A responsible system documents its "
            "training data, reports performance per subgroup, exposes a route to challenge a "
            "decision, and can be audited. Interpretability techniques such as feature "
            "importance and surrogate models help, and they connect back to the ranking ideas in "
            "[[data-visualization]] where each factor can be shown to a user."
        ),
    },
    {
        "slug": "ml-supervised-learning",
        "title": "Supervised Learning: Labelled Data and Loss Functions",
        "category": "Machine Learning",
        "author": "Prof. R. Menon",
        "url": "nexasearch://ml-supervised-learning",
        "keywords": "supervised learning, classification, regression, loss function, gradient descent",
        "content": (
            "Supervised learning fits a model to pairs of inputs and known outputs. "
            "Classification predicts a discrete label, regression predicts a continuous value.\n\n"
            "The learning objective is to minimise a loss function that measures the discrepancy "
            "between prediction and target. Squared error is natural for regression but its "
            "gradient grows with the error, so outliers dominate. Binary cross-entropy suits "
            "classification because its logarithm strongly penalises confident wrong answers. "
            "Its gradient simplifies to the predicted probability minus the true label, which is "
            "why gradient descent on cross-entropy is numerically stable.\n\n"
            "Optimisation is iterative because the loss surface of a neural network has many "
            "local minima. Batch gradient descent uses the whole dataset per step and is stable "
            "but slow. Stochastic gradient descent uses one example and is noisy but fast. "
            "Mini-batch gradient descent, with batches of tens to hundreds, is the practical "
            "compromise.\n\n"
            "The hypothesis class bounds what can be learned. Linear models cannot represent "
            "interactions, decision trees can but may overfit, and nearest-neighbour methods "
            "have no parameters at all. Choosing the class is the real modelling decision; the "
            "optimiser is comparatively routine. Evaluation discipline is described in "
            "[[ml-model-evaluation]] and data preparation in [[ml-feature-engineering]]."
        ),
    },
    {
        "slug": "ml-unsupervised-learning",
        "title": "Unsupervised Learning: Clustering and Dimensionality Reduction",
        "category": "Machine Learning",
        "author": "Prof. R. Menon",
        "url": "nexasearch://ml-unsupervised-learning",
        "keywords": "unsupervised learning, k-means, clustering, pca, dimensionality reduction",
        "content": (
            "Unsupervised learning works with unlabelled data. Its two goals are to discover "
            "structure, usually by grouping similar points, and to compress by discarding "
            "redundant dimensions.\n\n"
            "K-means partitions data into k clusters by alternating two steps: assign each point "
            "to the nearest centroid, then recompute each centroid as the mean of its members. "
            "Each iteration cannot increase the objective, so the algorithm terminates, but it "
            "can converge to a poor local optimum and it needs k in advance. Choosing k is often "
            "done with the elbow method or a silhouette score.\n\n"
            "K-means assumes roughly spherical clusters of similar size, so density-based methods "
            "such as DBSCAN, which can find arbitrarily shaped clusters and reject outliers, are "
            "often a better fit.\n\n"
            "Principal component analysis finds the directions of maximum variance by computing "
            "eigenvectors of the covariance matrix. Keeping the first k components minimises "
            "reconstruction error under a linear constraint. PCA is efficient for moderate "
            "dimensions, but computing eigenvectors is O(n * d^2) for d dimensions, so very "
            "wide data usually needs randomised or incremental methods.\n\n"
            "Unsupervised results are hard to validate because there is no ground truth; "
            "stability across resamples and usefulness for a downstream task are the practical "
            "criteria."
        ),
    },
    {
        "slug": "ml-deep-learning",
        "title": "Deep Learning Architectures and Their Costs",
        "category": "Machine Learning",
        "author": "S. Kulkarni",
        "url": "nexasearch://ml-deep-learning",
        "keywords": "deep learning, cnn, rnn, transformer, attention, computational cost",
        "content": (
            "Deep learning is the use of multilayer neural networks whose representations are "
            "learned rather than engineered.\n\n"
            "Convolutional networks exploit locality and translation invariance. Filters slide "
            "over the input and share weights, so the parameter count depends on the filter size "
            "rather than the image size. Pooling or strided convolutions reduce spatial size, "
            "which lets depth grow while compute stays manageable.\n\n"
            "Recurrent networks process sequences with a hidden state carried across time steps. "
            "Training them sequentially is slow and vanishing gradients hurt long ranges. The "
            "long short-term memory cell and the gated recurrent unit were designed specifically "
            "to mitigate that problem.\n\n"
            "Transformers removed recurrence entirely by making attention the only interaction "
            "between positions. Self-attention computes three matrices, queries, keys and "
            "values, and returns a weighted average of values with weights given by a scaled "
            "dot product of queries and keys. Cost per layer is O(L^2 * d) for sequence length L, "
            "so long documents are expensive, which motivated sparse and linear attention "
            "variants.\n\n"
            "Training cost is dominated by matrix multiplication: roughly six floating point "
            "operations per multiply-accumulate, doubled for forward and backward. Estimating "
            "and reducing this cost is a large part of practice, as described in "
            "[[ai-neural-networks-basics]]."
        ),
    },
    {
        "slug": "ml-model-evaluation",
        "title": "Evaluating Models: Bias, Variance and the Metrics That Matter",
        "category": "Machine Learning",
        "author": "Prof. R. Menon",
        "url": "nexasearch://ml-model-evaluation",
        "keywords": "model evaluation, precision, recall, f1 score, confusion matrix, cross validation",
        "content": (
            "A model that is not measured cannot be improved, and a model measured on the wrong "
            "data is measured wrongly. Evaluation has two independent parts: choosing the data "
            "split and choosing the metric.\n\n"
            "Train, validation and test sets should be disjoint. Because samples are often "
            "correlated, a random split can leak information; grouping by patient, user or time "
            "period is usually correct. K-fold cross-validation rotates the folds so every "
            "example is used for testing once, and it costs k times the training run.\n\n"
            "For classification the confusion matrix is the primitive. Accuracy is misleading on "
            "imbalanced data. Precision is the fraction of positive predictions that are "
            "correct, recall the fraction of true positives that are found, and the F1 score "
            "their harmonic mean, which punishes imbalance between the two. Area under the "
            "precision-recall curve is the right summary when positives are rare; area under "
            "the receiver operating characteristic curve is the right one when the operating "
            "point is not fixed.\n\n"
            "Underfitting means high bias: the model cannot represent the pattern. Overfitting "
            "means high variance: it memorised noise. The gap between training and validation "
            "error diagnoses which one is happening. Regularisation, early stopping and more "
            "data all attack variance; a richer hypothesis class attacks bias."
        ),
    },
    {
        "slug": "ml-feature-engineering",
        "title": "Feature Engineering and the Curse of Dimensionality",
        "category": "Machine Learning",
        "author": "S. Kulkarni",
        "url": "nexasearch://ml-feature-engineering",
        "keywords": "feature engineering, feature selection, scaling, curse of dimensionality, one hot encoding",
        "content": (
            "Features are the inputs a model sees, and in most tabular problems they matter more "
            "than the learning algorithm.\n\n"
            "Raw values rarely need no transformation. Numeric features usually need scaling: "
            "standardisation subtracts the mean and divides by the standard deviation, while "
            "min-max scaling maps to a fixed interval. Without scaling, distance-based methods "
            "and regularised linear models are dominated by whichever feature has the largest "
            "units. Categorical variables become indicator columns or embeddings. Text becomes "
            "counts, weights or embeddings, which connects directly to the term weighting ideas "
            "in [[string-matching-algorithms]] and to ranking.\n\n"
            "Feature selection reduces noise and cost. Filter methods score features "
            "independently of the model, wrapper methods search subsets using model performance "
            "at an exponential cost, and embedded methods such as L1 regularisation select "
            "during training.\n\n"
            "The curse of dimensionality says that as the number of dimensions grows, data "
            "becomes sparse and nearest-neighbour distances concentrate: in high dimensions the "
            "ratio between the largest and smallest distances shrinks towards one. Consequences "
            "are exponential growth in the volume needed to cover the space, meaningful "
            "deterioration of distance-based methods, and a proliferation of almost collinear "
            "combinations of features. Mitigations are feature selection, supervised projection "
            "methods, and simply collecting more data."
        ),
    },
    {
        "slug": "data-science-process",
        "title": "The Data Science Process from Question to Decision",
        "category": "Data Science",
        "author": "N. Iyer",
        "url": "nexasearch://data-science-process",
        "keywords": "data science process, problem framing, hypothesis, deployment, cross functional",
        "content": (
            "Data science is often described as a sequence of steps, but the order matters more "
            "than the labels. The process starts with a question that someone will actually act "
            "on. A precise question has a population, an outcome, a time window and a decision "
            "attached to it.\n\n"
            "Only then does data collection begin. Collecting is easy to over-engineer; a small, "
            "correctly labelled sample answers a question faster than a large, noisy one. "
            "Exploration follows, and its purpose is to find surprises: distributions, "
            "correlations, missingness patterns and outright impossible values.\n\n"
            "Preparation is where most of the real work lives: cleaning, joining, reshaping and "
            "deriving features. Statistical analysis then tests whether the pattern is "
            "distinguishable from noise, with the caution that many comparisons on the same data "
            "will look significant by chance.\n\n"
            "Model building is iterative, and the loop is short: build, measure, adjust. "
            "Communication is continuous rather than a final step, because a result nobody "
            "understands cannot change a decision.\n\n"
            "Deployment is where projects are usually abandoned. Monitoring must track both "
            "prediction quality and input drift, and a model that cannot be rolled back is not "
            "finished. Governance of the deployed system is described in [[ai-ethics]] and its "
            "operational counterpart in [[devops-fundamentals]]."
        ),
    },
    {
        "slug": "statistics-for-data-science",
        "title": "Statistics for Data Science: Estimation, Testing and Correlation",
        "category": "Data Science",
        "author": "N. Iyer",
        "url": "nexasearch://statistics-for-data-science",
        "keywords": "statistics, mean, variance, standard deviation, p-value, correlation",
        "content": (
            "Descriptive statistics summarise a sample. The mean is the arithmetic average, the "
            "median is the middle value and is robust to outliers, and the mode is the most "
            "frequent value. Spread is measured by the range, the interquartile range, the "
            "variance and the standard deviation. The variance is the average squared deviation "
            "from the mean, so it is measured in squared units and must be square-rooted to be "
            "interpretable.\n\n"
            "Because the variance uses squared deviations it is sensitive to outliers, which is "
            "why robust alternatives exist. Reporting only a mean without a spread is the most "
            "common reporting error in analysis.\n\n"
            "Inference estimates a population from a sample. A confidence interval expresses the "
            "plausible range of an estimate; a hypothesis test asks whether observed data would "
            "be surprising under a null model. The p-value is the probability of data at least "
            "as extreme as what was observed, given the null. It is not the probability that the "
            "null is true, a misunderstanding that causes most over-claiming.\n\n"
            "Correlation measures linear association, usually with the Pearson coefficient "
            "between minus one and one. It is scale invariant but not robust: an outlier can "
            "dominate it. Correlation is not causation, and two variables can correlate strongly "
            "because of a third or by coincidence. Distribution shape is covered in "
            "[[data-visualization]] and preparation in [[data-cleaning]]."
        ),
    },
    {
        "slug": "data-visualization",
        "title": "Data Visualisation Principles for Honest Communication",
        "category": "Data Science",
        "author": "Dr. M. Fernandes",
        "url": "nexasearch://data-visualization",
        "keywords": "data visualization, bar chart, scatter plot, misleading charts, dashboard",
        "content": (
            "A chart is an argument made with geometry, so chart design is partly an ethics "
            "question. Truncating a bar axis exaggerates differences; a dual axis creates "
            "apparent correlation between unrelated series; colour scales that ignore the data "
            "range hide structure.\n\n"
            "Choosing the mark follows the question. Comparison of categories uses bars or dots "
            "on a common baseline. Change over time uses lines, with a truthful time axis. "
            "Distribution uses histograms, box plots or violin plots. Relationship between two "
            "numeric variables uses a scatter plot. Composition uses stacked bars, and readers "
            "should compare segments only when they share a common baseline.\n\n"
            "Colour has jobs: categorical hues separate groups, sequential ramps encode ordered "
            "values, and diverging ramps show deviation around a meaningful midpoint. Roughly "
            "eight percent of men have some colour vision deficiency, so red-green pairs are a "
            "poor default and redundant encodings such as shape or direct labels are safer.\n\n"
            "Dashboards are for monitoring a small number of known questions, with a fixed "
            "layout read repeatedly. Exploratory analysis wants flexibility. Both must show the "
            "uncertainty, not just the point estimate, and every number should be traceable to "
            "the query that produced it."
        ),
    },
    {
        "slug": "data-cleaning",
        "title": "Data Cleaning: Missing Values, Outliers and Duplicates",
        "category": "Data Science",
        "author": "N. Iyer",
        "url": "nexasearch://data-cleaning",
        "keywords": "data cleaning, missing values, outliers, duplicates, validation",
        "content": (
            "Cleaning is the step everyone skips and everybody needs. Three problems dominate.\n\n"
            "Missing data has three mechanisms: missing completely at random, missing at random "
            "given observed values, and missing not at random, where the value itself depends on "
            "the process. Deleting rows is safe only in the first case. Imputation with the mean "
            "or median is acceptable for the second and distorts the distribution otherwise. For "
            "the third, a missingness indicator is often the most informative feature available.\n\n"
            "Outliers are values that are far from the bulk. Robust detection uses the "
            "interquartile range, defining outliers beyond one and a half times the interquartile "
            "range from the first and third quartiles, or a median absolute deviation. Treat them "
            "as errors only when a domain rule says so; a hundredfold revenue outlier is often "
            "the most important row in the data.\n\n"
            "Duplicates arise from repeated measurement, joining on a non-unique key, and "
            "inconsistent identifiers. Hashing a normalised row is a cheap way to detect exact "
            "duplicates, and near duplicates need token or attribute similarity instead, which is "
            "the same idea the search engine uses for [[string-matching-algorithms]].\n\n"
            "Validation rules should be declarative and run in a pipeline: types, ranges, "
            "referential integrity and uniqueness."
        ),
    },
    {
        "slug": "cloud-computing-models",
        "title": "Cloud Service Models: IaaS, PaaS and SaaS",
        "category": "Cloud Computing",
        "author": "R. Castellan",
        "url": "nexasearch://cloud-computing-models",
        "keywords": "cloud computing, iaas, paas, saas, shared responsibility, elasticity",
        "content": (
            "Cloud computing delivers computing resources over a network as a metered service. "
            "Three service models differ in how much management the customer keeps.\n\n"
            "Infrastructure as a Service gives virtual machines, storage and networking. The "
            "provider manages the physical layer and virtualisation; the customer manages the "
            "operating system, runtime and data. This gives the most control and the most "
            "responsibility, and it suits workloads with unusual requirements or existing "
            "operating-system expertise, as described in [[operating-systems-concepts]].\n\n"
            "Platform as a Service gives a managed runtime: databases, queues, schedules and "
            "deployment pipelines. The customer supplies only code and data. This removes most "
            "operational work at the cost of portability, because the platform APIs are "
            "proprietary.\n\n"
            "Software as a Service is the finished application, reached through a browser or API. "
            "The provider owns everything, including availability, patching and scaling.\n\n"
            "The shared responsibility model states exactly who secures what. In IaaS the "
            "customer secures the guest operating system onwards; in SaaS the customer secures "
            "only identity and data. Misreading this boundary is the most common cause of cloud "
            "security incidents, which is why [[cybersecurity-fundamentals]] treats it "
            "explicitly.\n\n"
            "Elasticity, the ability to grow capacity on demand and shrink it back, is the "
            "economic argument for moving to the cloud."
        ),
    },
    {
        "slug": "cloud-architecture-patterns",
        "title": "Cloud Architecture Patterns and Trade-offs",
        "category": "Cloud Computing",
        "author": "R. Castellan",
        "url": "nexasearch://cloud-architecture-patterns",
        "keywords": "cloud architecture, load balancing, microservices, database replication, caching",
        "content": (
            "Architecture in the cloud is a set of recurring patterns, each trading cost "
            "against control or latency.\n\n"
            "Load balancing distributes requests across instances, spreading load, failing over "
            "and enabling rolling deployment. Round robin is simple but ignores capacity, least "
            "connections suits long requests, and consistent hashing keeps affinity for cacheable "
            "sessions.\n\n"
            "Microservices split a system into independently deployed services. They allow "
            "independent scaling and team autonomy, at the price of network calls that become "
            "failure points, distributed transactions that are hard to reason about, and far "
            "more operational surface. A monolith is often the correct starting point.\n\n"
            "Caching sits at several layers: in-process, shared cache, content delivery network. "
            "Each layer removes work from the layer behind it, and each introduces an invalidation "
            "problem. A time-to-live is the simplest correct policy.\n\n"
            "Database replication keeps a readable copy, which improves query performance and "
            "availability. Replication lag means a read after a write may be stale, so read "
            "routing must be chosen deliberately. Message queues decouple producers from "
            "consumers and provide buffering, at-least-once delivery and retry with backoff.\n\n"
            "Designing for failure means assuming any component can fail, adding timeouts and "
            "circuit breakers, and keeping a coherent story about what the user sees while a "
            "region is unavailable."
        ),
    },
    {
        "slug": "serverless-computing",
        "title": "Serverless Computing and Function-as-a-Service",
        "category": "Cloud Computing",
        "author": "R. Castellan",
        "url": "nexasearch://serverless-computing",
        "keywords": "serverless, function as a service, cold start, event driven, autoscaling",
        "content": (
            "Serverless means the customer manages no servers at all. The platform allocates, "
            "patches and scales capacity per request, and the customer pays only for invocations "
            "and duration.\n\n"
            "The unit of execution is a function invoked by an event: an HTTP request, a queue "
            "message or a schedule. The programming model is stateless, so anything that must "
            "persist goes into a database or object store. This is a direct constraint on design, "
            "not merely a convenience.\n\n"
            "Cold start is the delay between an invocation and execution while the platform "
            "starts an instance. It is paid on the first request after idle time, and it is why "
            "latency-sensitive endpoints need provisioned concurrency.\n\n"
            "Autoscaling reacts to a metric such as concurrency or queue depth. Scaling too "
            "slowly causes a backlog; scaling too quickly wastes money and can oscillate, so "
            "hysteresis matters.\n\n"
            "Function size and duration limits are real constraints, and very long jobs belong in "
            "a workflow engine or a queue consumer. Serverless composes well with event-driven "
            "pipelines and is a poor fit for sustained high utilisation with steady load, where "
            "reserved capacity is cheaper."
        ),
    },
    {
        "slug": "containers-in-cloud",
        "title": "Containers and Orchestration in the Cloud",
        "category": "Cloud Computing",
        "author": "P. Sandhu",
        "url": "nexasearch://containers-in-cloud",
        "keywords": "container, docker, kubernetes, orchestration, immutable deployment",
        "content": (
            "A container packages an application with its dependencies into a single image that "
            "runs identically on any host with a compatible kernel. The mechanism is operating "
            "system namespaces, which isolate the view of the filesystem, processes and network, "
            "plus control groups, which limit CPU and memory.\n\n"
            "The decisive property is immutability. An image is built once and promoted through "
            "environments without modification, so what runs in production is byte-for-byte what "
            "was tested. Tagging with the commit hash and deploying by digest makes rollbacks "
            "trivial.\n\n"
            "A container is not a virtual machine: it shares the host kernel, so it starts in "
            "milliseconds rather than seconds but cannot run a different kernel.\n\n"
            "An orchestrator schedules containers, heals them when they fail, and manages "
            "service discovery, scaling and rolling updates. Kubernetes represents desired state "
            "declaratively and continuously reconciles reality towards it, which means the "
            "controller loop, not the operator, is what guarantees consistency.\n\n"
            "Image size affects pull time and therefore scale-up latency, so multi-stage builds "
            "and minimal base images matter. Layer caching and image registries close the loop "
            "with the pipelines described in [[continuous-integration]]."
        ),
    },
]
