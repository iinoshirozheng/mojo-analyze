# Pinned-CPU contention: matched-region clock control (2026-11-27)

## Question and scope

Can a continuously runnable competitor on the **same pinned logical CPU**, without a voluntary sleep in the timed kernel, enlarge wall time without a corresponding increase in thread CPU time? This is a controlled methodology check for the unresolved ARM64 checked-Span scanner modes, not a Mojo performance measurement. Nov 25 calibrated injected sleep and setup work; Nov 26 measured dual-clock instrumentation cost. Today varies scheduler contention instead. The canonical ARM64 experiment remains blocked locally (x86_64, no Mojo or Pixi). Main inspected at 31c0d15d559f141f34bd845744d98b5dacb0ccef.

## Method and results

Linux x86_64 container, AMD EPYC 9V74, GCC Debian 14.2.0-19, affinity initially CPUs 0–4, parent and children pinned to CPU 0. Same optimized C binary in both conditions. Kernel: 40 million unsigned 64-bit recurrence iterations, independent affine-composition checksum oracle. One warm-up per condition and 25 paired trials with seeded randomized within-pair order. Contended condition starts a separate continuously runnable Python process on the same logical CPU, verifies its affinity and readiness, and checks /proc/PID/stat CPU ticks increased over the probe invocation. Competitor startup and teardown outside timed region. Baseline does not launch competitor. No guarantee of exclusive host hardware; competitor CPU ticks include probe launch/exit and have 10 ms resolution. All 52 kernel checksum checks passed: 4831745506076715521; all 26 contended invocations had positive competitor tick deltas (retained trials 4–6 ticks, median 5, CLK_TCK=100).

| Condition | Wall median (range), ms | Thread CPU median (range), ms | Wall minus CPU median (range), ms |
|---|---:|---:|---:|
| Baseline | 45.5758 (44.4488–52.1553) | 45.5687 (44.4222–52.1208) | 0.0301 (0.0020–0.0533) |
| Contended | 93.4101 (87.4886–99.5805) | 45.2821 (44.3904–47.1955) | 48.0211 (42.8068–52.3850) |

Paired contended-minus-baseline median wall +47.880699 ms (42.078651–51.867430, 25/25 positive); thread CPU -0.197871 ms (-4.925277–2.257414, 11/25 positive); wall-minus-CPU +47.982626 ms (42.774812–52.350455, 25/25 positive). No claim of equivalence or precise CPU-frequency attribution. Same binary and instruction path; objdump main calls clock helper at 0x10aa/0x10b7, work at 0x10c2, clock helper at 0x10cf/0x10dc. Work loop 0x1250–0x125e contains imul/add/cmp/jne. Binary SHA256 e8493da3329ead58f038f68cc80d18016b8d3987688a6cd770e05e68982de5d8.

## Reproduction

Save as probe.c:
~~~c
#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>
#include <time.h>
static uint64_t ns(clockid_t c){ struct timespec t; if(clock_gettime(c,&t)) exit(2); return (uint64_t)t.tv_sec*1000000000+t.tv_nsec; }
__attribute__((noinline)) static uint64_t work(uint64_t x, uint64_t n){for(uint64_t i=0;i<n;i++) x=x*UINT64_C(6364136223846793005)+UINT64_C(1442695040888963407); return x;}
int main(int argc,char **argv){if(argc!=2)return 2; uint64_t n=strtoull(argv[1],0,10); uint64_t w0=ns(CLOCK_MONOTONIC),c0=ns(CLOCK_THREAD_CPUTIME_ID); uint64_t x=work(1,n); uint64_t c1=ns(CLOCK_THREAD_CPUTIME_ID),w1=ns(CLOCK_MONOTONIC); printf("%" PRIu64 " %" PRIu64 " %" PRIu64 "\n",x,w1-w0,c1-c0);}
~~~
Save as run.py:
~~~python
import os,sys,subprocess,random,statistics as st
N=40_000_000
M=(1<<64)-1
n=N;a,b=6364136223846793005,1442695040888963407;x=1
while n:
    if n&1:x=(a*x+b)&M
    a,b=a*a&M,(a*b+b)&M;n>>=1
cpu=min(os.sched_getaffinity(0));os.sched_setaffinity(0,{cpu})
def ticks(pid):
    f=open(f'/proc/{pid}/stat').read().rsplit(')',1)[1].split()
    return int(f[11])+int(f[12])
def trial(contended):
    p=None
    try:
        if contended:
            p=subprocess.Popen([sys.executable,'-c','print("ready",flush=True)\nwhile True: pass'],stdout=subprocess.PIPE,text=True)
            assert p.stdout.readline().strip()=='ready'
            assert os.sched_getaffinity(p.pid)=={cpu}
            t=ticks(p.pid)
        checksum,w,c=map(int,subprocess.check_output(['./probe',str(N)],text=True).split())
        assert checksum==x and w>0 and c>0
        d=ticks(p.pid)-t if p else 0
        if p: assert d>0
        return w/1e6,c/1e6,(w-c)/1e6,d
    finally:
        if p:p.terminate();p.wait();p.stdout.close()
for mode in (False,True):trial(mode)
r=random.Random(1127); rows=[]
for _ in range(25):
    order=[False,True];r.shuffle(order);z={m:trial(m) for m in order};rows.append((z[False],z[True]))
print('CPU',cpu,'checksum',x,'CLK_TCK',os.sysconf('SC_CLK_TCK'))
for j,name in enumerate(('baseline','contended')):
    print(name,[(round(st.median(a),4),round(min(a),4),round(max(a),4)) for a in zip(*(z[j] for z in rows))])
for j,name in enumerate(('wall','thread_cpu','gap')):
    d=[b[j]-a[j] for a,b in rows];print('paired',name,st.median(d),min(d),max(d),sum(v>0 for v in d))
print('raw',rows)
~~~
Run:
~~~sh
cc -O3 -Wall -Wextra -Werror probe.c -o probe
python run.py
objdump -d probe
sha256sum probe
~~~

## Interpretation

Pinning alone does not eliminate scheduler contention. A continuously runnable competing process creates a distinct wall-minus-thread-CPU signature in this controlled single-threaded workload, unlike an increase in on-CPU work. The difference is not an exact measure of scheduler waiting because clock boundaries and accounting differ. CPU time is not cycles, instructions or frequency. The result is a positive control for future ARM64 matched-region experiments, not evidence that contention causes the Mojo scanner modes. Re-run both controls on the actual target runner, preserve checksum and assembly, and collect region-scoped dual clocks and, if available, hardware counters. No canonical benchmarks, rankings or results changed.
