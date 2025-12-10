## Algorithm features

t := current tick, as a positive integer value in {0, N} for a timewheel of size N

t_c_k := minimum wait time for callback c

t_c_exp := expiration date for callback c

t_safe := global safety margin for inserts in ticks for the timewheel

t_c_l := tcexp - tsafe  upper bound for the insertion window offset

x mod N := { x for 0 < x < N } U { remainder(x / N) for x > N}

 insert new callback c at tc = min( {(t + t_c_k) mod N < t` <= (t + t_c_l ) mod N} )

## Target system features

- no missed deadline 

- all callbacks get spread out evenly, within available timeframe for each (guaranteed by 7. in the algorithm features)

Extra note: the system has several parameters, such as the safety margin for ticks, the number of seconds per tick (time granularity) and the scale of each timewheel (f.e. “0-60 seconds” or “1-48 hours” ).  These have to be manually set beforehand to tune the system for expected callback volume and deadlines.

## Theoretical system capacity
The system makes concurrent calls (actions) every tick. Every tick has some defined timeframe in seconds and thus a maximum theoretical capacity of work that can be done per tick. We want to know this theoretical upper bound so we can prevent the system from going over capacity. In order to do this we want to know the maximum total actions *n* that can be performed in every tick, given some number of concurrent workers *c* and the average expected completion time for each actions *s*.

### Background
A simple model for computing the theoretical limit of concurrent systems doing actions that have I/O wait times is **throughput**. Since this is not an exact relationship, we use ~ to denote 'scales linearly with', instead of = .

> (1) *tp ~ c / s*

Where tp = throughput, c = concurrency (number of workers) and s = seconds it takes to complete an action. This defines how many actions the system can complete per second. Given the throughput we can compute the **total runtime** given some total number of actions.

> (2) *tr ~ n / tp + cput*

Where *n* is the total number of actions and *cput* is the total execution overhead required to run all workers. This is determined by the single-thread speed of the code itself, not including the waiting for I/O. Then if we want to compute some target total number of actions given the other values:

> (3) *n ~ (tr - cput) * tp*

### Our system
works slightly differently, as it has to complete a set A of *n* actions per worker before it can move on to the next task. Each action in that set belongs to a different class. Each class is expected to have it's own average response time. Once that set is complete, the worker will have completed |A| tasks. This means our adjusted throughput will be:

> (4) *tp ~ c / s_T * |A|*

Where *s_T* is the total time necessary to complete all actions in A

> (5) *s_T = s_1 + s_2 + ... + s_n* where *n = |A|*

The each *s_k* in *{s_1, ..., s_n}* corresponds to the average expected response time of action class *k*.

### Final formula
Combining (3) and (4) we can compute our theoretical total actions given the number of concurrent workers, our sets of actions and their expected average response times as:

> (6) n ~ (tr - cput) * c / s_T * |A| 

Since this value is based on correlative relationships, it will not precisely follow real world behavior. The values of *tr* and *|A|* are known exactly beforehand. We ideally want *c* as large as possible and *cput* as small as possible. They depends on the computer system specs and programming language. In practice they have to be determined by measuring runtime metrics. *s_T* is a combined value of multiple action classes. The best way to compute it's value is also from real world metrics.

### Using the formula
Using this formula we can compute the theoretical number of action sets we can complete per tick of the timewheel, by setting *tr* to the time of one tick. We have to stay within that limit. By continuously re-computing it based on real world metrics we can (auto) adjust the parameters of our system to stay within that limit, for example by increasing the number of OS threads and spreading work accross them.


Our system currently has a set of two actions *A* = {update_keyvault, call_auth_endpoint} to complete per worker.

