import matplotlib.pyplot as plt

plt.imshow(canvas.original_img, cmap="gray")
colors = ["r","g","b","y","c","m"]

for i in range(6):
    mask = sector_masks[:, :, i]
    plt.contour(mask, colors=colors[i], linewidths=1)
    plt.text(cx, cy - rad_3mm + 20*i, f"S{i+1}", color=colors[i])

plt.scatter(cx, cy, c="white")
plt.show()