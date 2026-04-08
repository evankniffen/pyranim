import matplotlib.pyplot as plt

ys = [
      1,
      1,
      1,
      2,
      2,
      3,
      5,
      6,
      8,
      12,
      17,
      23,
      33,
      45,
      62,
      89,
      122,
      169,
      235,
      321,
      438,
      589,
      776,
      1006,
      1277,
      1576,
      1894,
      2219,
      2524,
      2805,
      3041,
      3226,
      3350,
      3425,
      3440,
      3405,
      3326,
      3211,
      3068,
      2900,
      2717,
      2523,
      2330,
      2127,
      1932,
      1743,
      1563,
      1388,
      1229,
      1077,
      943,
      815,
      702,
      599,
      511,
      429,
      360,
      299,
      248,
      201,
      164,
      131,
      106,
      83,
      65,
      50,
      40,
      29,
      22,
      16,
      12,
      8,
      6,
      4,
      3,
      2,
      1,
      1,
      1
]

n=12
xs = list(range(n * (n + 1) // 2 + 1))

plt.figure(figsize=(16, 10))
plt.bar(xs, ys, width=0.8)
plt.xlabel("Number of chips")
plt.ylabel("Number of isomorphism classes")
plt.title(f"Isomorphism classes by chip count (n_tiers={n})")
plt.xticks(xs)
plt.tight_layout()
#plt.show()
filename = f"tempgraph"
plt.savefig(filename, dpi=500)
plt.close()

fail = False
for i in xs:
    if (i != 0) and (i != n * (n + 1) // 2):
        if ys[i-1] * ys[i+1] > ys[i]*ys[i]:
            print("fail log concavity at ", i)
            fail = True

if not fail:
    print("sucess log concavity")