# Matched-region CPU-clock instrumentation cost (2026-11-26)

## Question

Following [2026-11-25-region-cpu-clock-calibration.md](2026-11-25-region-cpu-clock-calibration.md), what marginal overhead does adding two CLOCK_THREAD_CPUTIME_ID reads inside an existing monotonic wall-clock bracket introduce? This is a preparatory calibration for the ARM64 checked-Span scanner, not another scanner data reanalysis or a Mojo benchmark. No native Mojo, Pixi or ARM64 available. Baseline main 643056a9a1cd3fff3b518c184f6b602abba966e4; canonical CONTRIBUTING and ANALYSIS inspected, including outstanding Category D scanner and Linux arm64 Sieve codegen hypotheses.

## Method and correctness

Linux x86_64, AMD EPYC 9V74, kernel 6.18.57, glibc 2.41, GCC 14.2.0, Python 3.13.5. One optimized C binary, two modes, identical noinline recurrence of 256 iterations per region, 20,000 regions per process. Both modes bracket with CLOCK_MONOTONIC; dual mode reads CLOCK_THREAD_CPUTIME_ID just before/after work. Outer monotonic bracket measures aggregate cost including timing, checks and accumulation, excluding process launch and printing. Divide by 20,000; independent trials are processes, not inner regions. Two discarded warmups, 25 seeded randomly ordered pairs (50 retained processes). Independent affine-exponentiation oracle verifies 5,120,000 recurrence iterations for each process. All 52/52 checksums equal 11316503638258163713; clock intervals nonnegative and aggregate nesting checks pass. Optimized objdump verifies the same work symbol at 0x1390, a 256-iteration multiply/add loop, called at 0x1146 and 0x1216. Wall-only path has clock calls 0x1128/0x1156; dual adds calls to ns at 0x120b/0x1223 inside outer region clock reads 0x11e7/0x1235. Binary SHA256 ba001ebb714387e9b59ac306d5d4e9474c2aa10567c8e48448bbc17a52dce9c6.

## Results

Nanoseconds per region, median across 25 processes (min–max).

| Mode | Outer elapsed / region | Inner wall / region | Inner CPU / region |
|---|---:|---:|---:|
| Wall only | 340.33 (320.76–405.88) | 315.62 (297.20–377.01) | not measured |
| Dual | 594.98 (564.01–781.28) | 569.13 (539.52–746.44) | 417.34 (394.68–522.12) |

Paired outer elapsed delta median +266.94 ns (176.14–457.69), positive in all 25 pairs. Paired inner wall delta median +266.06 ns. Paired deltas in order (ns): 216.24,335.84,217.52,214.58,281.06,299.50,254.66,238.43,254.37,176.14,266.94,275.55,291.54,222.20,295.79,457.69,211.94,282.96,239.18,265.66,279.24,305.28,273.04,268.72,211.79.

## Reproduction

Save probe.c:
~~~c
#define _POSIX_C_SOURCE 200809L
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <inttypes.h>
static uint64_t ns(clockid_t id) {
  struct timespec t;
  if(clock_gettime(id,&t)) {perror("clock_gettime");exit(2);}
  return (uint64_t)t.tv_sec*1000000000ULL+(uint64_t)t.tv_nsec;
}
__attribute__((noinline)) static uint64_t work(uint64_t x) {
  for(unsigned j=0;j<256;j++) x=x*6364136223846793005ULL+1442695040888963407ULL;
  return x;
}
int main(int argc,char**argv){
  if(argc!=2 || (argv[1][0]!='0' && argv[1][0]!='1') || argv[1][1])return 2;
  int dual=argv[1][0]=='1';
  uint64_t x=1, sw=0,sc=0;
  const unsigned N=20000;
  uint64_t outer=ns(CLOCK_MONOTONIC);
  for(unsigned i=0;i<N;i++){
    uint64_t w0=ns(CLOCK_MONOTONIC),c0=0,c1=0;
    if(dual)c0=ns(CLOCK_THREAD_CPUTIME_ID);
    x=work(x);
    if(dual)c1=ns(CLOCK_THREAD_CPUTIME_ID);
    uint64_t w1=ns(CLOCK_MONOTONIC);
    if(w1<w0 || c1<c0)return 3;
    sw+=w1-w0; sc+=c1-c0;
  }
  uint64_t end=ns(CLOCK_MONOTONIC);
  if(end<=outer)return 3;
  printf("%"PRIu64" %"PRIu64" %"PRIu64" %"PRIu64"\n",x,end-outer,sw,sc);
}
~~~
Save audit.py:
~~~python
import random, subprocess, statistics as s
N=20000; A=6364136223846793005; B=1442695040888963407; M=(1<<64)-1
n=N*256;a,b=1,0;p,q=A,B
while n:
    if n&1:a,b=p*a&M,(p*b+q)&M
    p,q=p*p&M,(p*q+q)&M;n>>=1
expected=(a+b)&M
def one(mode):
    x,outer,w,c=map(int,subprocess.check_output(['./probe',str(mode)],text=True).split())
    assert x==expected and outer>=w>0 and (0<c<=w if mode else c==0)
    return outer/N,w/N,c/N
for m in (0,1):one(m)
r=random.Random(20261126); rows=[]
for _ in range(25):
    order=[0,1];r.shuffle(order); d={m:one(m) for m in order};rows.append((d[0],d[1]))
print('expected',expected,'verified',52)
for mode in (0,1):
    print(mode,[(round(s.median(v),2),round(min(v),2),round(max(v),2)) for v in zip(*(x[mode] for x in rows))])
diff=[b[0]-a[0] for a,b in rows]
print('paired outer ns per bracket delta',s.median(diff),min(diff),max(diff),'positive',sum(x>0 for x in diff))
print('paired inner wall ns delta',s.median(b[1]-a[1] for a,b in rows))
print('raw',diff)
~~~
~~~sh
gcc -std=c11 -O3 -Wall -Wextra -Werror probe.c -o probe
python audit.py
sha256sum probe
objdump -d --disassemble=main probe
objdump -d --disassemble=work probe
~~~

## Conclusion and limits

Adding dual reads has observable cost for sub-microsecond regions on this host. The paired measurement is incremental instrumentation cost, not an isolated clock_gettime latency: loop paths, check/accumulation, scheduling and clock implementation differ. The wall bracket contains CPU-clock calls while the CPU bracket excludes some of them, so their difference is not pure descheduling. For the scanner, bracket once around the full region rather than per byte; calibrate on actual ARM64 Mojo binary and confirm same checksum and hot assembly; keep uninstrumented baseline and report measured overhead instead of subtracting an x86 estimate. This shared x86 host and small C kernel cannot establish native ARM64 overhead, hardware cycles, codegen causes or scanner speed. No canonical performance conclusions, results or charts changed.
