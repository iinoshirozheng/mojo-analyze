# Region-scoped CPU clock calibration (2026-11-25)

## Question and scope

Can a matched-region thread CPU clock distinguish pre-region CPU work from an in-region off-CPU delay? This is one preparatory methodology experiment for the unresolved ARM64 checked-Span scanner bimodality, not a Mojo speed comparison. The September 24 diagnostic (Actions run [35985827133](https://github.com/iinoshirozheng/mojo-analyze/actions/runs/35985827133)) showed slow-minus-fast scanner wall time +0.245949 s and whole-child CPU time +0.243482 s, but their scopes differ. The CPU delta could include setup. The November 23 and 24 adjacency and execution-slot audits do not solve that attribution problem.

## Method

Linux x86_64, AMD EPYC 9V74, kernel 6.18.57, glibc 2.41, GCC 14.2.0, Python 3.13.5. No native ARM64, Mojo or Pixi available. C11 unsigned 64-bit recurrence, identical 5 million iterations within each region, with three controlled conditions: baseline (5M setup iterations), extra setup (40M setup iterations before both timers), and 50 ms nanosleep inside both timers (5M setup). Read CLOCK_MONOTONIC and CLOCK_THREAD_CPUTIME_ID around the region; parent separately reads RUSAGE_CHILDREN user + system delta. One discarded warmup per condition, 15 shuffled blocks with each condition once (seed 20261125), 45 retained trials. Independent O(log n) affine composition oracle verifies both setup and region checksums for every invocation (48/48). Region and normal setup checksum 2672771704063622465; extra setup checksum 4831745506076715521. Reject nonpositive times and checksum errors. No performance claim across languages or architectures.

## Observations

All values milliseconds; median across 15 trials, ranges in parentheses.

| Condition | Region wall | Region thread CPU | Whole-child CPU |
|---|---:|---:|---:|
| Baseline | 5.6699 (5.5065–6.7752) | 5.6686 (5.5053–6.7740) | 12.440 (11.708–14.540) |
| Extra setup | 5.7994 (5.5413–9.6371) | 5.7976 (5.5396–9.6339) | 52.818 (51.498–64.178) |
| In-region sleep | 55.7547 (55.6306–56.0846) | 5.6758 (5.5515–6.0099) | 12.252 (12.006–13.855) |

Extra setup minus baseline median: +0.1296 wall, +0.1290 thread CPU, +40.378 whole-child CPU. Sleep minus baseline: +50.0848 wall, +0.0071 thread CPU, -0.188 whole-child CPU. Directional calibration assertions passed (setup whole-child CPU delta >15 ms, region CPU delta magnitude <10 ms; sleep wall delta >40 ms, region CPU delta magnitude <10 ms). These are loose sanity checks, not precision equivalence tests. Disassembly (objdump -d --disassemble=main) of the actual optimized binary shows setup loop at 0x1140 preceding clock calls at 0x115a/0x1167; region loop at 0x1190, conditional nanosleep at 0x11cc, then clock calls at 0x11da/0x11e7. Both recurrence loops retained in their intended scopes.

Binary SHA256: cef4617f592580ee5931d942946634d363d9b50f84b5c1f0bd5ec23093d67c50.

## Reproduction

Save as clock_probe.c:

~~~c
#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <errno.h>
#include <inttypes.h>
#include <string.h>
static uint64_t ns(clockid_t c) {
  struct timespec t;
  if (clock_gettime(c, &t)) { perror("clock_gettime"); exit(2); }
  return (uint64_t)t.tv_sec*1000000000u+(uint64_t)t.tv_nsec;
}
static uint64_t work(uint64_t n) {
  uint64_t x = 1;
  for(uint64_t i=0;i<n;i++) x=x*6364136223846793005ULL+1442695040888963407ULL;
  return x;
}
int main(int argc,char **argv) {
  if(argc!=2) return 2;
  int mode=atoi(argv[1]); if(mode<0||mode>2) return 2;
  uint64_t setup=work(mode==1?40000000:5000000);
  uint64_t w0=ns(CLOCK_MONOTONIC), c0=ns(CLOCK_THREAD_CPUTIME_ID);
  uint64_t result=work(5000000);
  if(mode==2){struct timespec t={0,50000000};while(nanosleep(&t,&t)){if(errno!=EINTR){perror("nanosleep");return 2;}}}
  uint64_t c1=ns(CLOCK_THREAD_CPUTIME_ID),w1=ns(CLOCK_MONOTONIC);
  printf("%" PRIu64 " %" PRIu64 " %" PRIu64 " %" PRIu64 "\n",result,setup,w1-w0,c1-c0);
}
~~~

Save as audit.py:

~~~python
import random, resource, subprocess, statistics, platform
N=5_000_000
MASK=(1<<64)-1
A=6364136223846793005; B=1442695040888963407
# Independent affine exponentiation oracle, O(log n), not the C loop.
def oracle(n):
    a,b=1,0; p,q=A,B
    while n:
        if n&1: a,b=(p*a)&MASK,(p*b+q)&MASK
        p,q=(p*p)&MASK,(p*q+q)&MASK
        n>>=1
    return (a+b)&MASK

def cpu():
    r=resource.getrusage(resource.RUSAGE_CHILDREN)
    return r.ru_utime+r.ru_stime

def one(m):
    c0=cpu(); out=subprocess.check_output(['./clock_probe',str(m)],text=True); c1=cpu()
    checksum,setup,w,c=map(int,out.split())
    assert checksum==oracle(N) and setup==oracle(40_000_000 if m==1 else N)
    assert w>0 and c>0
    return w/1e6,c/1e6,(c1-c0)*1000

for m in range(3): one(m)
rng=random.Random(20261125); results=[[] for _ in range(3)]
for _ in range(15):
    order=list(range(3));rng.shuffle(order)
    for m in order: results[m].append(one(m))
print(platform.platform(), 'checksums',oracle(N),oracle(40_000_000))
for i,rows in enumerate(results):
    print(i, 'median', [round(statistics.median(c),4) for c in zip(*rows)], 'ranges',[(round(min(c),4),round(max(c),4)) for c in zip(*rows)])
base,setup,sleep=[list(map(statistics.median,zip(*x))) for x in results]
print('delta setup', [round(y-x,4) for x,y in zip(base,setup)])
print('delta sleep', [round(y-x,4) for x,y in zip(base,sleep)])
assert setup[2]-base[2]>15 and abs(setup[1]-base[1])<10
assert sleep[0]-base[0]>40 and abs(sleep[1]-base[1])<10
~~~

~~~sh
cc -std=c11 -O3 -Wall -Wextra -Werror clock_probe.c -o clock_probe
python audit.py
objdump -d --disassemble=main clock_probe
~~~

## Conclusion and next action

Matched-region thread CPU time plus wall time distinguishes these two deliberately injected confounds on this single-threaded Linux x86_64 fixture. Whole-child CPU time cannot attribute work to the scanner when setup differs. This supports instrumenting both clocks inside the native ARM64 scanner, rechecking clock semantics and overhead, checksum, compiler and disassembly, and randomized interleaving. Thread CPU time is not hardware cycles or instruction counts; cannot by itself distinguish frequency, pipeline stalls and executed work while scheduled. For multi-threaded workloads choose the appropriate worker/process scope. Nested clock bracket includes reads in wall interval; quantify instrumentation overhead on target. Shared host and one calibration session; no universal timing precision guarantee. Professor (today's radar) is an external candidate, not tested here. No native Mojo timing, ranking, or change to canonical results, charts or ANALYSIS.md.
